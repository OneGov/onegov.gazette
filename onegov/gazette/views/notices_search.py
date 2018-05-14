from datetime import datetime
from morepath.request import Response
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import CategoryCollection
from onegov.gazette.collections import OrganizationCollection
from onegov.gazette.collections import PublishedNoticeCollection
from onegov.gazette.layout import Layout
from onegov.gazette.pdf import Pdf


@GazetteApp.html(
    model=PublishedNoticeCollection,
    template='search.pt',
    permission=Public
)
def view_search(self, request):
    """ Search the published notices. """

    layout = Layout(self, request)

    orderings = {
        'first_issue': {
            'title': _("Issue(s)"),
            'href': request.link(self.for_order('first_issue')),
            'sort': self.direction if self.order == 'first_issue' else '',
        },
        'organization': {
            'title': _("Organization"),
            'href': request.link(self.for_order('organization')),
            'sort': self.direction if self.order == 'organization' else '',
        },
        'category': {
            'title': _("Category"),
            'href': request.link(self.for_order('category')),
            'sort': self.direction if self.order == 'category' else '',
        },
        'title': {
            'title': _("Title"),
            'href': request.link(self.for_order('title')),
            'sort': self.direction if self.order == 'title' else '',
        },
    }

    categories = CategoryCollection(request.session).as_options()
    categories = [
        (value, title, value in (self.categories or []))
        for value, title in categories
    ]

    organizations = OrganizationCollection(request.session).as_options()
    organizations = [
        (value, title, value in (self.organizations or []))
        for value, title in organizations
    ]

    clear = None
    if any((
        self.term, self.categories, self.organizations,
        self.from_date, self.to_date
    )):
        target = self.for_dates(None, None)
        target = target.for_term(None)
        target = target.for_organizations(None)
        target = target.for_categories(None)
        clear = request.link(target)

    return {
        'layout': layout,
        'notices': self.batch,
        'term': self.term,
        'categories': categories,
        'organizations': organizations,
        'from_date': self.from_date,
        'to_date': self.to_date,
        'orderings': orderings,
        'clear': clear,
        'pdf': request.link(self, name='pdf')
    }


@GazetteApp.view(
    model=PublishedNoticeCollection,
    name='pdf',
    permission=Public
)
def view_search_pdf(self, request):
    """ Download the search results as PDF. """

    pdf = Pdf.from_collection(self, request)

    filename = normalize_for_url(
        '{}-{}-{}-{}'.format(
            request.translate(_("Gazette")),
            request.app.principal.name,
            request.translate(_("Search Results")),
            datetime.now().isoformat()
        )
    )

    return Response(
        pdf.read(),
        content_type='application/pdf',
        content_disposition=f'inline; filename={filename}.pdf'
    )