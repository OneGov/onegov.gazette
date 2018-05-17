from datetime import datetime
from io import BytesIO
from morepath.request import Response
from onegov.core.security import Private
from onegov.core.utils import normalize_for_url
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.collections.notices import TRANSLATIONS
from onegov.gazette.layout import Layout
from xlsxwriter import Workbook


@GazetteApp.html(
    model=GazetteNoticeCollection,
    template='statistics.pt',
    name='statistics',
    permission=Private
)
def view_notices_statistics(self, request):
    """ View the list of notices.
    This view is only visible by a publisher. This (in the state 'accepted')
    is the view used by the publisher.
    """

    layout = Layout(self, request)
    filters = (
        {
            'title': _(state),
            'link': request.link(self.for_state(state), name='statistics'),
            'class': 'active' if state == self.state else ''
        }
        for state in (
            'drafted', 'submitted', 'accepted', 'rejected', 'published'
        )
    )

    return {
        'layout': layout,
        'filters': filters,
        'collection': self,
        'title': _("Statistics"),
        'from_date': self.from_date,
        'to_date': self.to_date,
        'by_organizations': self.count_by_organization(),
        'by_category': self.count_by_category(),
        'by_groups': self.count_by_group(),
        'rejected': self.count_rejected(),
        'clear': request.link(self.for_dates(None, None), name='statistics')
    }


@GazetteApp.view(
    model=GazetteNoticeCollection,
    name='statistics-xlsx',
    permission=Private
)
def view_notices_statistics_xlsx(self, request):
    """ View the statistics as XLSX. """

    output = BytesIO()
    workbook = Workbook(output)
    for title, row, content in (
        (_("Organizations"), _("Organization"), self.count_by_organization),
        (_("Categories"), _("Category"), self.count_by_category),
        (_("Groups"), _("Group"), self.count_by_group),
        (_("Rejected"), _("Name"), self.count_rejected),
    ):
        worksheet = workbook.add_worksheet()
        worksheet.name = request.translate(title)
        worksheet.write_row(0, 0, (
            request.translate(row),
            request.translate(_("Count"))
        ))
        for index, row in enumerate(content()):
            worksheet.write_row(index + 1, 0, row)
    workbook.close()
    output.seek(0)

    response = Response()
    response.content_type = (
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response.content_disposition = 'inline; filename={}-{}-{}.xlsx'.format(
        request.translate(_("Statistics")).lower(),
        normalize_for_url(request.translate(TRANSLATIONS.get(self.state, ''))),
        datetime.utcnow().strftime('%Y%m%d%H%M')
    )
    response.body = output.read()

    return response
