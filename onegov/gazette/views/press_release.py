from morepath import redirect
from morepath.request import Response
from onegov.core.security import Personal
from onegov.core.utils import normalize_for_url
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import PressReleaseCollection
from onegov.gazette.forms import EmptyForm
from onegov.gazette.forms import PressReleaseForm
from onegov.gazette.layout import Layout
from onegov.gazette.models import PressRelease
from onegov.gazette.pdf import Pdf
from onegov.gazette.views import get_user_and_group
from webob.exc import HTTPForbidden


@GazetteApp.html(
    model=PressRelease,
    template='press_release.pt',
    permission=Personal
)
def view_press_release(self, request):
    """ View a press release.

    View the press release and its meta data. This is the main view for the
    press releases to do the state changes.

    """

    layout = Layout(self, request)

    user_ids, group_ids = get_user_and_group(request)
    editor = request.is_personal(self)
    publisher = request.is_private(self)
    admin = request.is_secret(self)
    owner = self.user_id in user_ids
    same_group = self.group_id in group_ids

    def _action(label, name, class_, target='_self'):
        return (label, request.link(self, name), class_, target)

    action = {
        'accept': _action(_("Accept"), 'accept', 'primary'),
        'attachments': _action(_("Attachments"), 'attachments', 'secondary'),
        'copy': (
            _("Copy"),
            request.link(
                PressReleaseCollection(
                    request.session,
                    state=self.state,
                    source=self.id
                ), name='new-press-release'
            ),
            'secondary',
            '_self'
        ),
        'delete': _action(_("Delete"), 'delete', 'alert right'),
        'edit': _action(_("Edit"), 'edit', 'secondary'),
        'preview': _action(_("Preview"), 'preview', 'secondary', '_blank'),
        'publish': _action(_("Publish"), 'publish', 'primary'),
        'reject': _action(_("Reject"), 'reject', 'alert right'),
        'submit': _action(_("Submit"), 'submit', 'primary'),
        'view': _action(_("View"), 'view', 'secondary', '_blank'),
    }

    actions = []
    if self.state == 'drafted' or self.state == 'rejected':
        if publisher or (editor and (same_group or owner)):
            actions.append(action['submit'])
            actions.append(action['edit'])
            actions.append(action['delete'])
            actions.append(action['attachments'])
        if publisher:
            actions.append(action['view'])
    elif self.state == 'submitted':
        if publisher:
            actions.append(action['accept'])
            actions.append(action['edit'])
            actions.append(action['reject'])
            actions.append(action['attachments'])
            actions.append(action['view'])
        if admin:
            actions.append(action['delete'])
    elif self.state == 'accepted':
        if publisher:
            actions.append(action['publish'])
        actions.append(action['copy'])
        if admin:
            actions.append(action['edit'])
            actions.append(action['attachments'])
            actions.append(action['delete'])
        if publisher:
            actions.append(action['view'])
    elif self.state == 'published':
        actions.append(action['copy'])
        if admin:
            actions.append(action['edit'])
            actions.append(action['attachments'])
        actions.append(action['view'])

    actions.append(action['preview'])

    return {
        'layout': layout,
        'press_release': self,
        'actions': actions,
        'publisher': publisher
    }


@GazetteApp.html(
    model=PressRelease,
    template='press_release_preview.pt',
    name='preview',
    permission=Personal
)
def preview_press_release(self, request):
    """ Preview the press release. """

    layout = Layout(self, request)

    return {
        'layout': layout,
        'press_release': self,
        'export': request.link(self, name='preview-pdf')
    }


@GazetteApp.view(
    model=PressRelease,
    name='preview-pdf',
    permission=Personal
)
def preview_press_release_pdf(self, request):
    """ Preview the press release as PDF. """

    pdf = Pdf.from_press_release(self, request)
    filename = normalize_for_url(self.title)
    return Response(
        pdf.read(),
        content_type='application/pdf',
        content_disposition=f'inline; filename={filename}.pdf'
    )


@GazetteApp.form(
    model=PressRelease,
    name='edit',
    template='form.pt',
    permission=Personal,
    form=PressReleaseForm
)
def edit_press_release(self, request, form):
    """ Edit a press release.

    This view is used by the editors and publishers. Editors may only edit
    their own press releases, publishers may edit any press release. It's not
    possible to change already accepted or published press releases.

    """

    layout = Layout(self, request)
    is_private = request.is_private(self)

    if not is_private:
        user_ids, group_ids = get_user_and_group(request)
        if not ((self.group_id in group_ids) or (self.user_id in user_ids)):
            raise HTTPForbidden()

    if self.invalid_organization:
        request.message(
            _(
                "The press release has an invalid organization. "
                "Please re-select the organization."
            ),
            'warning'
        )

    if form.submitted(request):
        form.update_model(self)
        self.add_change(request, _("edited"))
        request.message(_("Press release modified."), 'success')
        return redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Edit Press Release"),
        'helptext': _(
            "The fields marked with an asterisk * are mandatory fields."
        ),
        'button_text': _("Save"),
        'cancel': request.link(self)
    }


@GazetteApp.form(
    model=PressRelease,
    name='delete',
    template='form.pt',
    permission=Personal,
    form=EmptyForm
)
def delete_press_release(self, request, form):
    """ Delete a press release.

    Only drafted or rejected press releases may be deleted (usually by
    editors). Editors may only delete their own press releases, publishers may
    delete any press release.

    It is possible for admins to delete submitted and accepted press release
    too.

    """
    layout = Layout(self, request)
    is_admin = request.is_secret(self)

    if not request.is_private(self):
        user_ids, group_ids = get_user_and_group(request)
        if not ((self.group_id in group_ids) or (self.user_id in user_ids)):
            raise HTTPForbidden()

    if (
        self.state == 'published' or
        (self.state in ('submitted', 'accepted') and not is_admin)
    ):
        request.message(
            _(
                "Only drafted or rejected press releases may be deleted."
            ),
            'alert'
        )
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Delete Press Release"),
            'show_form': False
        }

    if self.state == 'accepted':
        request.message(
            _("This press release has already been accepted!"), 'warning'
        )

    if form.submitted(request):
        collection = PressReleaseCollection(request.session)
        collection.delete(self)
        request.message(_("Press release deleted."), 'success')
        return redirect(layout.dashboard_or_press_releases_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Delete Press Release"),
        'button_text': _("Delete Press Release"),
        'button_class': 'alert',
        'cancel': request.link(self)
    }
