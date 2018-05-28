from onegov.form import Form
from onegov.gazette import _
from onegov.gazette.collections import OrganizationCollection
from onegov.gazette.fields import DateTimeLocalField
from onegov.gazette.fields import SelectField
from onegov.gazette.views import get_user
from onegov.quill import QuillField
from sedate import standardize_date
from sedate import to_timezone
from wtforms import HiddenField
from wtforms import StringField
from wtforms.validators import InputRequired
from wtforms.validators import Length


class PressReleaseForm(Form):
    """ Edit a press relase.

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

    text = QuillField(
        label=_("Text"),
        tags=('strong', 'ol', 'ul'),
        validators=[
            InputRequired()
        ]
    )

    issue_date = DateTimeLocalField(
        label=_("Issue date"),
        validators=[
            InputRequired()
        ]
    )

    timezone = HiddenField()

    def on_request(self):
        session = self.request.session

        self.timezone.data = self.request.app.principal.time_zone

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

    def update_model(self, model):
        model.title = self.title.data
        model.organization_id = self.organization.data
        model.text = self.text.data
        model.issue_date = self.issue_date.data
        # Convert the deadline from the local timezone to UTC
        if model.issue_date:
            model.issue_date = standardize_date(
                model.issue_date, self.timezone.data
            )
        model.apply_meta(self.request.session)

    def apply_model(self, model):
        self.title.data = model.title
        self.organization.data = model.organization_id
        self.text.data = model.text
        self.issue_date.data = model.first_issue
        # Convert the deadline from UTC to the local timezone
        if self.issue_date.data:
            self.issue_date.data = to_timezone(
                self.issue_date.data, self.timezone.data
            ).replace(tzinfo=None)