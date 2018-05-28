from morepath.request import Response
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.layout import Layout
from onegov.gazette.models import GazetteNotice
from onegov.gazette.pdf import Pdf
from webob.exc import HTTPForbidden


@GazetteApp.html(
    model=GazetteNotice,
    template='notice_published.pt',
    name='view',
    permission=Public
)
def view_published_notice(self, request):
    """ View the published notice. """

    if not self.state == 'published' or self.expired:
        if not request.is_private(self):
            raise HTTPForbidden()

    layout = Layout(self, request)

    return {
        'layout': layout,
        'notice': self,
        'pdf': request.link(self, name='pdf')
    }


@GazetteApp.html(
    model=GazetteNotice,
    template='notice_embed.pt',
    name='embed',
    permission=Public
)
def view_published_notices_embed(self, request):
    """ Show the the published notice embeddable. """

    if not self.state == 'published' or self.expired:
        raise HTTPForbidden()

    layout = Layout(self, request)

    return {
        'layout': layout,
        'notice': self,
        'pdf': request.link(self, name='pdf')
    }


@GazetteApp.view(
    model=GazetteNotice,
    name='pdf',
    permission=Public
)
def view_published_notice_pdf(self, request):
    """ View the published notice as PDF. """

    if not self.state == 'published' or self.expired:
        if not request.is_private(self):
            raise HTTPForbidden()

    pdf = Pdf.from_notice(self, request)

    filename = normalize_for_url(
        '{}-{}-{}'.format(
            request.translate(_("Gazette")),
            request.app.principal.name,
            self.title
        )
    )

    return Response(
        pdf.read(),
        content_type='application/pdf',
        content_disposition=f'inline; filename={filename}.pdf'
    )
