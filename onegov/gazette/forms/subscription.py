from onegov.form import Form
from onegov.gazette import _
from wtforms import HiddenField
from wtforms import StringField
from wtforms.validators import Email
from wtforms.validators import InputRequired


class SubscriptionForm(Form):

    email = StringField(
        label=_("E-Mail"),
        validators=[
            InputRequired(),
            Email()
        ]
    )


class SubscriptionConfirmationForm(Form):

    token = HiddenField()
