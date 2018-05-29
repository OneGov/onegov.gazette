from datetime import datetime
from io import BytesIO
from json import dumps
from morepath import redirect
from morepath.request import Response
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.core.utils import normalize_for_url
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.forms import EmptyForm
from onegov.gazette.forms import NoticeForm
from onegov.gazette.layout import Layout
from onegov.gazette.models import GazetteNotice
from onegov.gazette.pdf import Pdf
from onegov.gazette.views import get_user
from onegov.gazette.views import get_user_and_group
from sedate import to_timezone
from xlsxwriter import Workbook


@GazetteApp.form(
    model=GazetteNoticeCollection,
    name='new-notice',
    template='form.pt',
    permission=Personal,
    form=NoticeForm
)
def create_notice(self, request, form):
    """ Create a new notice.

    If a valid UID of a notice is given (via 'source' query parameter), its
    values are pre-filled in the form.

    This view is mainly used by the editors.

    """

    layout = Layout(self, request)

    if form.submitted(request):
        notice = self.add(
            title=form.title.data,
            text=form.text.data,
            author_place=form.author_place.data,
            author_date=form.author_date_utc,
            author_name=form.author_name.data,
            organization_id=form.organization.data,
            category_id=form.category.data,
            print_only=form.print_only.data if form.print_only else False,
            at_cost=form.at_cost.data == 'yes',
            billing_address=form.billing_address.data,
            user=get_user(request),
            issues=form.issues.data
        )
        return redirect(request.link(notice))

    if not form.errors and self.source:
        source = self.query().filter(GazetteNotice.id == self.source).first()
        if source:
            form.apply_model(source)
            if form.print_only:
                form.print_only.data = False

    return {
        'layout': layout,
        'form': form,
        'title': _("New Official Notice"),
        'helptext': _(
            "The fields marked with an asterisk * are mandatory fields."
        ),
        'button_text': _("Save"),
        'cancel': layout.dashboard_or_notices_link,
        'current_issue': layout.current_issue
    }


@GazetteApp.html(
    model=GazetteNoticeCollection,
    template='notices.pt',
    permission=Personal
)
def view_notices(self, request):
    """ View the list of notices.

    This view is only visible by a publisher. This (in the state 'accepted')
    is the view used by the publisher.

    """

    layout = Layout(self, request)
    is_publisher = request.is_private(self)
    is_admin = request.is_secret(self)

    states = ['drafted', 'submitted', 'accepted', 'published', 'rejected']
    if is_admin:
        states.append('imported')

    filters = (
        {
            'title': _(state),
            'link': request.link(self.for_state(state)),
            'class': 'active' if state == self.state else ''
        }
        for state in states
    )

    orderings = {
        'title': {
            'title': _("Title"),
            'href': request.link(self.for_order('title')),
            'sort': self.direction if self.order == 'title' else '',
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
        'group': {
            'title': _("Group"),
            'href': request.link(self.for_order('group.name')),
            'sort': self.direction if self.order == 'group.name' else '',
        },
        'user': {
            'title': _("User"),
            'href': request.link(self.for_order('user.name')),
            'sort': self.direction if self.order == 'user.name' else '',
        },
        'first_issue': {
            'title': _("Issue(s)"),
            'href': request.link(self.for_order('first_issue')),
            'sort': self.direction if self.order == 'first_issue' else '',
        }
    }

    title = _("Official Notices")
    if not is_publisher:
        self.user_ids, self.group_ids = get_user_and_group(request)
        filters = None
        title = _("Published Official Notices")

    export_pdf = None
    export_index = None
    if is_publisher:
        export_pdf = request.link(self, name='export-pdf')
    if is_publisher and self.state == 'published':
        export_index = request.link(self, name='export-index')

    return {
        'layout': layout,
        'is_publisher': is_publisher,
        'notices': self.batch,
        'title': title,
        'filters': filters,
        'term': self.term,
        'from_date': self.from_date,
        'to_date': self.to_date,
        'orderings': orderings,
        'clear': request.link(self.for_dates(None, None).for_term(None)),
        'new_notice': request.link(self, name='new-notice'),
        'export_pdf': export_pdf,
        'export_index': export_index
    }


@GazetteApp.view(
    model=GazetteNoticeCollection,
    name='export-pdf',
    permission=Private
)
def view_notices_export_pdf(self, request):
    """ Export the notices as PDF.

    This view is only visible by a publisher.

    """

    pdf = Pdf.from_notices(self, request)

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


@GazetteApp.view(
    model=GazetteNoticeCollection,
    name='export-index',
    permission=Private
)
def view_notices_export_index(self, request):
    """ Export the index to the notices as PDF.

    This view is only visible by a publisher.

    """

    pdf = Pdf.index_from_notices(self, request)

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


@GazetteApp.form(
    model=GazetteNoticeCollection,
    name='update',
    template='form.pt',
    permission=Private,
    form=EmptyForm
)
def view_notices_update(self, request, form):
    """ Updates all notices (of this state): Applies the categories, issues and
    organization from the meta informations. This view is not used normally
    and only intended when changing category names in the principal definition,
    for example.

    """

    layout = Layout(self, request)
    session = request.session

    if form.submitted(request):
        for notice in self.query():
            notice.apply_meta(session)
        request.message(_("Notices updated."), 'success')

        return redirect(layout.dashboard_or_notices_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("Update notices"),
        'button_text': _("Update"),
        'cancel': layout.dashboard_or_notices_link
    }


@GazetteApp.view(
    model=GazetteNoticeCollection,
    name='export',
    permission=Private
)
def view_notices_export(self, request):
    """ Export all notices as XLSX. The exported file can be re-imported
    using the import-notices command line command.

    """

    output = BytesIO()
    workbook = Workbook(output, {
        'default_date_format': 'dd.mm.yy'
    })
    datetime_format = workbook.add_format({'num_format': 'dd.mm.yy hh:mm'})

    worksheet = workbook.add_worksheet()
    worksheet.name = request.translate(_("Official Notices"))
    worksheet.write_row(0, 0, (
        request.translate(_("Name")),
        request.translate(_("State")),
        request.translate(_("Source")),
        request.translate(_("Title")),
        request.translate(_("Text")),
        request.translate(_("Author Place")),
        request.translate(_("Author Date")),
        request.translate(_("Author Name")),
        request.translate(_("Issues")),
        request.translate(_("Expiry Date")),
        request.translate(_("Category")),
        request.translate(_("Organization")),
        request.translate(_("Print only")),
        request.translate(_("Liable to pay costs")),
        request.translate(_("Billing address"))
    ))

    timezone = request.app.principal.time_zone
    for index, notice in enumerate(self.for_state(None).query()):

        worksheet.write(index + 1, 0, notice.name)
        worksheet.write(index + 1, 1, notice.state)
        worksheet.write(index + 1, 2, notice.source)
        worksheet.write(index + 1, 3, notice.title)
        worksheet.write(index + 1, 4, notice.text)
        if notice.author_date:
            worksheet.write_datetime(
                index + 1, 5,
                to_timezone(notice.author_date, timezone).replace(tzinfo=None),
                datetime_format
            )
        else:
            worksheet.write(index + 1, 5, None)
        worksheet.write(index + 1, 6, notice.author_name)
        worksheet.write(index + 1, 7, notice.author_place)
        worksheet.write(index + 1, 8, dumps(dict(notice.issues)))
        if notice.expiry_date:
            worksheet.write_datetime(
                index + 1, 5,
                to_timezone(notice.expiry_date, timezone).replace(tzinfo=None),
                datetime_format
            )
        else:
            worksheet.write(index + 1, 9, None)
        worksheet.write(index + 1, 10, notice.category_id)
        worksheet.write(index + 1, 11, notice.organization_id)
        worksheet.write(index + 1, 12, True if notice.print_only else False)
        worksheet.write(index + 1, 13, True if notice.at_cost else False)
        worksheet.write(index + 1, 14, notice.billing_address)

    workbook.close()
    output.seek(0)

    response = Response()
    response.content_type = (
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response.content_disposition = 'inline; filename={}-{}.xlsx'.format(
        request.translate(_("Official Notices")).lower(),
        datetime.utcnow().strftime('%Y%m%d%H%M')
    )
    response.body = output.read()

    return response
