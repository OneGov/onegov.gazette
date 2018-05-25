from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.gazette import _
from wtforms import BooleanField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms.validators import InputRequired
from wtforms.validators import Length


class EmptyForm(Form):

    pass


class RejectForm(Form):

    comment = TextAreaField(
        label=_("Comment"),
        validators=[
            InputRequired()
        ],
        render_kw={'rows': 4}
    )


class ImportForm(Form):

    canton = StringField(
        label=_("Canton"),
        validators=[
            Length(max=2)
        ],
        default='SG'
    )

    subrubrics = MultiCheckboxField(
        label=_("Category"),
        choices=[
            ('KK01', 'KK01 – Vorläufige Konkursanzeige'),
            ('KK02', 'KK02 – Konkurspublikation/Schuldenruf'),
            ('KK03', 'KK03 – Einstellung des Konkursverfahrens')
        ],
        validators=[
            InputRequired()
        ]
    )

    clear = BooleanField(
        label=_("Clear"),
        default=False
    )
