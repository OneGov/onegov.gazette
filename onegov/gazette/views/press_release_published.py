from morepath.request import Response
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.gazette import GazetteApp
from onegov.gazette.layout import Layout
from onegov.gazette.models import PressRelease
from onegov.gazette.pdf import Pdf
from webob.exc import HTTPForbidden


@GazetteApp.html(
    model=PressRelease,
    template='press_release_published.pt',
    name='view',
    permission=Public
)
def view_published_press_release(self, request):
    """ View the published press release. """

    if not self.state == 'published':
        if not request.is_private(self):
            raise HTTPForbidden()

    layout = Layout(self, request)

    return {
        'layout': layout,
        'press_release': self,
        'pdf': request.link(self, name='pdf')
    }


@GazetteApp.view(
    model=PressRelease,
    name='pdf',
    permission=Public
)
def view_published_press_release_pdf(self, request):
    """ View the published press release as PDF. """

    if not self.state == 'published':
        if not request.is_private(self):
            raise HTTPForbidden()

    pdf = Pdf.from_press_release(self, request)
    filename = normalize_for_url(self.title)

    return Response(
        pdf.read(),
        content_type='application/pdf',
        content_disposition=f'inline; filename={filename}.pdf'
    )
