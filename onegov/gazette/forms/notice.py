from datetime import date
from onegov.form import Form
from onegov.gazette import _
from onegov.gazette.collections import CategoryCollection
from onegov.gazette.collections import OrganizationCollection
from onegov.gazette.fields import MultiCheckboxField
from onegov.gazette.fields import SelectField
from onegov.gazette.layout import Layout
from onegov.gazette.models import Issue
from onegov.gazette.views import get_user
from onegov.quill import QuillField
from sedate import as_datetime
from sedate import standardize_date
from sedate import utcnow
from wtforms import HiddenField
from wtforms import RadioField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired
from wtforms.validators import Length
from wtforms.validators import Optional


class NoticeForm(Form):
    """ Edit an official notice.

    The issues are limited according to the deadline (or the issue date in the
    for publishers) and the categories and organizations are limited to the
    active one.

    """

    title = StringField(
        label=_("Title (maximum 60 characters)"),
        validators=[
            InputRequired(),
            Length(max=60)
        ],
        render_kw={'maxlength': 60},
    )

    organization = SelectField(
        label=_("Organization"),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    category = SelectField(
        label=_("Category"),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    # mockup: was BooleanField
    print_only = HiddenField(
        label=_("Print only"),
        default=False
    )

    at_cost = RadioField(
        label=_("Liable to pay costs"),
        default='no',
        choices=[
            ('no', _("No")),
            ('yes', _("Yes"))
        ]
    )

    billing_address = TextAreaField(
        label=_("Billing address"),
        render_kw={'rows': 3},
        depends_on=('at_cost', 'yes')
    )

    issues = MultiCheckboxField(
        label=_("Issue(s)"),
        choices=[],
        validators=[
            InputRequired()
        ],
        limit=5
    )

    expiry_date = DateField(
        label=_("Expiry Date"),
        validators=[
            Optional()
        ]
    )

    text = QuillField(
        label=_("Text"),
        tags=('strong', 'ol', 'ul'),
        validators=[
            # mockup:
            # InputRequired()
        ],
        placeholders={
            'Rechtsmittelbelehrung': (
                'Gegen diese Wahl kann wegen Verletzung von Vorschriften '
                'über die politischen Rechte und ihre Ausübung innert 5 '
                'Tagen, von der Veröffentlichung an gerechnet, schriftlich '
                'Rekurs in Stimmrechtssachen beim Bezirksrat ... erhoben '
                'werden. Die Rekursschrift muss einen Antrag und dessen '
                'Begründung enthalten.'
            )
        },
        placeholder_label=_("Boilerplates")
    )

    author_place = StringField(
        label=_("Place"),
        validators=[
            InputRequired()
        ]
    )

    author_date = DateField(
        label=_("Date (usually the date of the issue)"),
        validators=[
            InputRequired()
        ]
    )

    author_name = TextAreaField(
        label=_("Author"),
        validators=[
            InputRequired()
        ],
        render_kw={'rows': 4},
    )

    @property
    def author_date_utc(self):
        if self.author_date.data:
            return standardize_date(as_datetime(self.author_date.data), 'UTC')
        return None

    @property
    def expiry_date_utc(self):
        if self.expiry_date.data:
            return standardize_date(as_datetime(self.expiry_date.data), 'UTC')
        return None

    def on_request(self):
        session = self.request.session

        # populate organization
        self.organization.choices = []
        self.organization.choices.append(
            ('', self.request.translate(_("Select one")))
        )
        self.organization.choices.extend(
            OrganizationCollection(session).as_options()
        )

        # mockup: added
        try:
            group = get_user(self.request).group
            if group:
                subset = [
                    (id_, name) for id_, name in self.organization.choices
                    if name == group.name
                ]
                if subset:
                    self.organization.choices = subset
        except AttributeError:
            pass

        # populate categories
        self.category.choices = CategoryCollection(session).as_options()

        # populate issues
        now = utcnow()
        layout = Layout(None, self.request)

        self.issues.choices = []
        query = session.query(Issue)
        query = query.order_by(Issue.date)
        if self.request.is_private(self.model):
            query = query.filter(date.today() < Issue.date)  # publisher
        else:
            query = query.filter(now < Issue.deadline)  # editor
        for issue in query:
            self.issues.choices.append((
                issue.name,
                layout.format_issue(issue, date_format='date_with_weekday')
            ))
            if now >= issue.deadline:
                self.issues.render_kw['data-hot-issue'] = issue.name

        # translate the string of the mutli select field
        self.issues.translate(self.request)
        self.text.translate(self.request)

        # Remove the print only option if not publisher
        if not self.request.is_private(self.model):
            self.delete_field('print_only')

    def update_model(self, model):
        model.title = self.title.data
        model.organization_id = self.organization.data
        model.category_id = self.category.data
        model.text = self.text.data
        model.author_place = self.author_place.data
        model.author_date = self.author_date_utc
        model.author_name = self.author_name.data
        model.at_cost = self.at_cost.data == 'yes'
        model.billing_address = self.billing_address.data
        model.issues = self.issues.data
        model.expiry_date = self.expiry_date_utc
        if self.print_only:
            model.print_only = self.print_only.data == 'True'
            # mockup: was model.print_only = self.print_only.data

        model.apply_meta(self.request.session)

    def apply_model(self, model):
        self.title.data = model.title
        self.organization.data = model.organization_id
        self.category.data = model.category_id
        self.text.data = model.text
        self.author_place.data = model.author_place
        self.author_date.data = model.author_date
        self.author_name.data = model.author_name
        self.at_cost.data = 'yes' if model.at_cost else 'no'
        self.billing_address.data = model.billing_address or ''
        self.issues.data = list(model.issues.keys())
        self.expiry_date.data = model.expiry_date
        if self.print_only:
            self.print_only.data = True if model.print_only else False


class UnrestrictedNoticeForm(NoticeForm):
    """ Edit an official notice without limitations on the issues, categories
    and organiaztions.

    Optionally disables the issues (e.g. if the notice is already published).

    """

    def on_request(self):
        session = self.request.session
        layout = Layout(None, self.request)

        def title(item):
            return item.title if item.active else '({})'.format(item.title)

        # populate organization
        self.organization.choices = []
        self.organization.choices.append(
            ('', self.request.translate(_("Select one")))
        )
        self.organization.choices.extend(
            OrganizationCollection(session).as_options(False)
        )

        # populate categories
        self.category.choices = CategoryCollection(session).as_options(False)

        # populate issues
        del self.issues.render_kw['data-limit']
        self.issues.choices = []
        query = session.query(Issue)
        query = query.order_by(Issue.date)
        for issue in query:
            self.issues.choices.append((
                issue.name,
                layout.format_issue(issue, date_format='date_with_weekday')
            ))

        # translate the string of the mutli select field
        self.issues.translate(self.request)
        self.text.translate(self.request)

    def disable_issues(self):
        self.issues.validators = []
        self.issues.render_kw['disabled'] = True

    def update_model(self, model):
        model.title = self.title.data
        model.organization_id = self.organization.data
        model.category_id = self.category.data
        model.text = self.text.data
        model.author_place = self.author_place.data
        model.author_date = self.author_date_utc
        model.author_name = self.author_name.data
        model.at_cost = self.at_cost.data
        if model.state != 'published':
            model.issues = self.issues.data
        model.expiry_date = self.expiry_date_utc

        model.apply_meta(self.request.session)
