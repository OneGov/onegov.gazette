from datetime import date
from datetime import timedelta
from onegov.form import Form
from onegov.form.fields import OrderedMultiCheckboxField
from onegov.gazette import _
from onegov.gazette.fields import HtmlField
from onegov.gazette.fields import SelectField
from onegov.gazette.layout import Layout
from onegov.gazette.models import UserGroup
from sqlalchemy import cast
from sqlalchemy import String
from wtforms import RadioField
from wtforms import StringField
from wtforms.validators import Email
from wtforms.validators import InputRequired


class EmptyForm(Form):

    pass


class UserForm(Form):

    role = RadioField(
        label=_("Role"),
        choices=[
            ('editor', _("Publisher")),
            ('member', _("Editor"))
        ],
        default='member',
        validators=[
            InputRequired()
        ]
    )

    group = SelectField(
        label=_("Group"),
        choices=[('', '')]
    )

    name = StringField(
        label=_("Name"),
        validators=[
            InputRequired()
        ]
    )

    email = StringField(
        label=_("E-Mail"),
        validators=[
            InputRequired(),
            Email()
        ]
    )

    def on_request(self):
        session = self.request.app.session()
        self.group.choices = session.query(
            cast(UserGroup.id, String), UserGroup.name
        ).all()
        self.group.choices.insert(0, ('', ''))

    def update_model(self, model):
        model.username = self.email.data
        model.role = self.role.data
        model.realname = self.name.data
        if not model.data:
            model.data = {}
        model.data['group'] = self.group.data

    def apply_model(self, model):
        self.email.data = model.username
        self.role.data = model.role
        self.name.data = model.realname
        self.group.data = (model.data or {}).get('group', '')


class UserGroupForm(Form):

    name = StringField(
        label=_("Name"),
        validators=[
            InputRequired()
        ]
    )

    def update_model(self, model):
        model.name = self.name.data

    def apply_model(self, model):
        self.name.data = model.name


class NoticeForm(Form):

    title = StringField(
        label=_("Title"),
        validators=[
            InputRequired()
        ]
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

    issues = OrderedMultiCheckboxField(
        label=_("Issue(s)"),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    text = HtmlField(
        label=_("Text"),
        validators=[
            InputRequired()
        ]
    )

    def on_request(self):
        principal = self.request.app.principal

        # populate organization
        self.organization.choices = list(principal.organizations.items())

        # populate categories
        self.category.choices = list(principal.categories.items())

        # populate issues
        self.issues.choices = []
        layout = Layout(None, self.request)
        today = date.today()
        max_date = today + timedelta(weeks=5)
        for date_, issue in principal.issues_by_date.items():
            if date_ < today:
                continue
            if date_ > max_date:
                break

            self.issues.choices.append(
                (
                    str(issue),
                    layout.format_issue(issue, date_format='date_with_weekday')
                )
            )

    def update_model(self, model):
        model.title = self.title.data
        model.organization_id = self.organization.data
        model.category_id = self.category.data
        model.text = self.text.data
        model.issues = self.issues.data
        model.apply_meta(self.request.app.principal)

    def apply_model(self, model):
        self.title.data = model.title
        self.organization.data = model.organization_id
        self.category.data = model.category_id
        self.text.data = model.text
        self.issues.data = list(model.issues.keys())


class RejectForm(Form):

    comment = StringField(
        label=_("Comment"),
        validators=[
            InputRequired()
        ]
    )
