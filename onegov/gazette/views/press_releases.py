from morepath import redirect
from onegov.core.security import Personal
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import PressReleaseCollection
from onegov.gazette.forms import PressReleaseForm
from onegov.gazette.layout import Layout
from onegov.gazette.models import PressRelease
from onegov.gazette.views import get_user
from onegov.gazette.views import get_user_and_group


@GazetteApp.form(
    model=PressReleaseCollection,
    name='new-press-release',
    template='form.pt',
    permission=Personal,
    form=PressReleaseForm
)
def create_press_release(self, request, form):
    """ Create a new press release.

    If a valid UID of a press release is given (via 'source' query parameter),
    its values are pre-filled in the form.

    This view is mainly used by the editors.

    """

    layout = Layout(self, request)

    if form.submitted(request):
        press_release = self.add(
            title=form.title.data,
            lead=form.lead.data,
            text=form.text.data,
            organization_id=form.organization.data,
            user=get_user(request),
            issue_date=form.issue_date.data,
            blocking_period=form.blocking_period.data,
            timezone=form.timezone.data,
            contact=form.contact.data,
            conference=form.conference.data
        )
        return redirect(request.link(press_release))

    if not form.errors and self.source:
        source = self.query().filter(PressRelease.id == self.source).first()
        if source:
            form.apply_model(source)

    return {
        'layout': layout,
        'form': form,
        'title': _("New Press Release"),
        'helptext': _(
            "The fields marked with an asterisk * are mandatory fields."
        ),
        'button_text': _("Save"),
        'cancel': layout.dashboard_or_notices_link
    }


@GazetteApp.html(
    model=PressReleaseCollection,
    template='press_releases.pt',
    permission=Personal
)
def view_press_releases(self, request):
    """ View the list of press releases.

    This view is only visible by a publisher. This (in the state 'accepted')
    is the view used by the publisher.

    """

    layout = Layout(self, request)
    is_publisher = request.is_private(self)

    filters = (
        {
            'title': _(state),
            'link': request.link(self.for_state(state)),
            'class': 'active' if state == self.state else ''
        }
        for state in (
            'drafted', 'submitted', 'accepted', 'rejected', 'published'
        )
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

    title = _("Press Releases")
    if not is_publisher:
        self.user_ids, self.group_ids = get_user_and_group(request)
        filters = None
        title = _("Published Press Releases")

    return {
        'layout': layout,
        'is_publisher': is_publisher,
        'press_releases': self.batch,
        'title': title,
        'filters': filters,
        'term': self.term,
        'from_date': self.from_date,
        'to_date': self.to_date,
        'orderings': orderings,
        'clear': request.link(self.for_dates(None, None).for_term(None)),
        'new_press_release': request.link(self, name='new-press-release')
    }
