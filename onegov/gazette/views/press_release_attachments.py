from morepath import redirect
from onegov.core.crypto import random_token
from onegov.core.security import Personal
from onegov.file.utils import as_fileintent
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.layout import Layout
from onegov.gazette.models import PressRelease
from onegov.gazette.models import GazetteNoticeFile
from webob import exc


# mockup: no group test for the new personal permission was added!


@GazetteApp.html(
    model=PressRelease,
    template='attachments.pt',
    name='attachments',
    permission=Personal  # mockup: was Private
)
def view_press_release_attachments(self, request):
    """ View all attachments to a single notice and allow to drop new
    attachments.

    Silently redirects to the notice view if the notice has already been
    accepted for non-admins.

    """

    layout = Layout(self, request)
    upload_url = layout.csrf_protected_url(request.link(self, name='upload'))

    if self.state == 'accepted' or self.state == 'published':
        if not request.is_secret(self):
            return redirect(request.link(self))

    return {
        'layout': layout,
        'title': self.title,
        'subtitle': _("Attachments"),
        'upload_url': upload_url,
        'files': self.files,
        'notice': self,
    }


@GazetteApp.view(
    model=PressRelease,
    name='upload',
    permission=Personal,  # mockup: was Private
    request_method='POST'
)
def press_release_upload_attachment(self, request):
    """ Upload an attachment and add it to the notice.

    Raises a HTTP 405 (Metho not Allowed) for non-admins if the notice has
    already been accepted.

    Raises a HTTP 415 (Unsupported Media Type) if the file format is not
    supported.

    """

    if self.state == 'accepted' or self.state == 'published':
        if not request.is_secret(self):
            raise exc.HTTPMethodNotAllowed()

    request.assert_valid_csrf_token()

    attachment = GazetteNoticeFile(id=random_token())
    attachment.name = request.params['file'].filename
    attachment.reference = as_fileintent(
        request.params['file'].file,
        request.params['file'].filename
    )

    if attachment.reference.content_type not in (
        'application/excel',
        'application/vnd.ms-excel',
        'application/msword',
        'application/pdf',
        'application/zip',
        'image/gif',
        'image/jpeg',
        'image/png',
        'image/x-ms-bmp',
        'text/plain'
    ):
        raise exc.HTTPUnsupportedMediaType()

    self.files.append(attachment)
    self.add_change(request, _("Attachment added."))

    request.message(_("Attachment added."), 'success')
    return redirect(request.link(self, 'attachments'))
