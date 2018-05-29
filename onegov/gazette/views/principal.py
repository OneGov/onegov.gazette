from datetime import timedelta
from morepath import redirect
from onegov.core.security import Personal
from onegov.core.security import Public
from onegov.core.security import Secret
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.collections import IssueCollection
from onegov.gazette.collections import PressReleaseCollection
from onegov.gazette.collections import PublishedNoticeCollection
from onegov.gazette.collections import PublishedPressReleaseCollection
from onegov.gazette.forms import ImportForm
from onegov.gazette.layout import Layout
from onegov.gazette.models import Issue
from onegov.gazette.models import Principal
from onegov.gazette.sogc import SogcImporter
from onegov.gazette.views import get_user_and_group
from sedate import utcnow


@GazetteApp.html(
    model=Principal,
    permission=Public,
    template='frontpage.pt',
)
def view_principal(self, request):
    """ The homepage.

    Redirects to the default management views according to the logged in role.

    Shows the home page if not logged-in.

    """

    layout = Layout(self, request)

    if request.is_private(self):
        return redirect(layout.manage_notices_link)

    if request.is_personal(self):
        return redirect(layout.dashboard_link)

    if not request.app.principal.show_archive:
        return redirect(layout.login_link)

    issues = IssueCollection(request.session)

    current_issue = issues.query().filter(Issue.date < utcnow())
    current_issue = current_issue.order_by(None).order_by(Issue.date.desc())
    current_issue = current_issue.first()

    next_issue = issues.query().filter(Issue.date > utcnow())
    next_issue = next_issue.order_by(None).order_by(Issue.date.desc())
    next_issue = next_issue.first()

    previous_issue = issues.query().filter(Issue.date < current_issue.date)
    previous_issue = previous_issue.order_by(None).order_by(Issue.date.desc())
    previous_issue = previous_issue.first()

    current_notices = PublishedNoticeCollection(request.session)
    current_notices = current_notices.for_dates(
        previous_issue.date + timedelta(days=1),
        current_issue.date
    )

    return {
        'layout': layout,
        'archive': request.link(self, name='archive'),
        'search': request.link(PublishedNoticeCollection(request.session)),
        'current_notices': request.link(current_notices),
        'press_releases': request.link(
            PublishedPressReleaseCollection(request.session)
        ),
        'current_issue': current_issue,
        'next_issue': next_issue
    }


@GazetteApp.html(
    model=Principal,
    permission=Public,
    name='archive',
    template='archive.pt',
)
def view_archive(self, request):
    """ The archive.

    Shows all the weekly PDFs by year.

    """
    layout = Layout(self, request)

    return {
        'layout': layout,
        'issues': IssueCollection(request.session).by_years(desc=True)
    }


@GazetteApp.html(
    model=Principal,
    permission=Personal,
    name='dashboard',
    template='dashboard.pt',
)
def view_dashboard(self, request):
    """ The dashboard view (for editors).

    Shows the drafted, submitted and rejected notices, shows warnings and
    allows to create a new notice.

    """

    layout = Layout(self, request)
    user_ids, group_ids = get_user_and_group(request)

    # Notices
    notices = GazetteNoticeCollection(
        request.session,
        user_ids=user_ids,
        group_ids=group_ids
    )
    rejected_notices = notices.for_state('rejected').query().all()
    drafted_notices = notices.for_state('drafted').query().all()
    submitted_notices = notices.for_state('submitted').query().all()
    new_notice = request.link(
        notices.for_state('drafted'),
        name='new-notice'
    )

    # Press releases
    press_releases = PressReleaseCollection(
        request.session,
        user_ids=user_ids,
        group_ids=group_ids
    )
    rejected_releases = press_releases.for_state('rejected').query().all()
    drafted_releases = press_releases.for_state('drafted').query().all()
    submitted_releases = press_releases.for_state('submitted').query().all()
    new_release = request.link(
        press_releases.for_state('drafted'),
        name='new-press-release'
    )

    # Warnings
    now = utcnow()
    limit = now + timedelta(days=2)
    past_issues_selected = False
    deadline_reached_soon = False
    for notice in drafted_notices:
        for issue in notice.issue_objects:
            if issue.deadline < now:
                past_issues_selected = True
            elif issue.deadline < limit:
                deadline_reached_soon = True
    if past_issues_selected:
        request.message(
            _("You have drafted messages with past issues."),
            'warning'
        )
    if deadline_reached_soon:
        request.message(
            _("You have drafted messages with issues close to the deadline."),
            'warning'
        )
    if rejected_notices or rejected_releases:
        request.message(_("You have rejected messages."), 'warning')

    return {
        'layout': layout,
        'title': _("Dashboard"),
        'rejected_notices': rejected_notices,
        'drafted_notices': drafted_notices,
        'submitted_notices': submitted_notices,
        'new_notice': new_notice,
        'rejected_releases': rejected_releases,
        'drafted_releases': drafted_releases,
        'submitted_releases': submitted_releases,
        'new_release': new_release,
        'current_issue': layout.current_issue
    }


@GazetteApp.form(
    model=Principal,
    name='sogc-import',
    template='form.pt',
    permission=Secret,
    form=ImportForm
)
def view_sogc_import(self, request, form):

    layout = Layout(self, request)

    if form.submitted(request):
        config = request.app.principal.sogc
        importer = SogcImporter(
            session=request.session,
            endpoint=config['endpoint'],
            username=config['username'],
            password=config['password'],
            canton=form.canton.data,
            rubrics=[],
            subrubrics=form.subrubrics.data
        )
        importer(
            clear=form.clear.data,
            accept=form.accept.data
        )
        request.message(_("Official notices imported."), 'success')
        return redirect(
            request.link(
                GazetteNoticeCollection(request.session).for_state('imported')
            )
        )

    return {
        'layout': layout,
        'form': form,
        'title': _("SOGC Import"),
        'button_text': _("Import"),
        'cancel': layout.homepage_link
    }
