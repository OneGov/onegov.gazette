from morepath import redirect
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.forms import EmptyForm
from onegov.gazette.forms import RejectForm
from onegov.gazette.forms import PublishPressReleaseForm
from onegov.gazette.layout import Layout
from onegov.gazette.models import PressRelease
from onegov.gazette.views import get_user_and_group
from webob.exc import HTTPForbidden


@GazetteApp.form(
    model=PressRelease,
    name='submit',
    template='form.pt',
    permission=Personal,
    form=EmptyForm
)
def submit_press_release(self, request, form):
    """ Submit a press release.

    This view is used by the editors to submit their drafts for the publishers
    to review.

    Only drafted press releases may be submitted. Editors may only submit their
    own press releases (publishers may submit any press release).

    If a press release has invalid has an invalid/inactive organization, the
    user is redirected to the edit view.

    """

    layout = Layout(self, request)
    is_private = request.is_private(self)

    if not is_private:
        user_ids, group_ids = get_user_and_group(request)
        if not ((self.group_id in group_ids) or (self.user_id in user_ids)):
            raise HTTPForbidden()

    if self.state != 'drafted' and self.state != 'rejected':
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Submit Press Release"),
            'callout': _(
                "Only drafted or rejected press releases may be submitted."
            ),
            'show_form': False
        }

    if self.invalid_organization:
        return redirect(request.link(self, name='edit'))

    if form.submitted(request):
        self.submit(request)
        request.message(_("Press release submitted."), 'success')
        return redirect(layout.dashboard_or_press_releases_link)

    return {
        'message': _(
            'Do you really want to submit "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Submit Press Release"),
        'button_text': _("Submit Press Release"),
        'cancel': request.link(self)
    }


@GazetteApp.form(
    model=PressRelease,
    name='accept',
    template='form.pt',
    permission=Private,
    form=EmptyForm
)
def accept_press_release(self, request, form):
    """ Accept a press release.

    This view is used by the publishers to accept a submitted press release.

    Only submitted press releases may be accepted.

    """

    layout = Layout(self, request)

    if self.state != 'submitted':
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Accept Press Release"),
            'callout': _("Only submitted press releases may be accepted."),
            'show_form': False
        }

    if self.invalid_organization:
        return redirect(request.link(self, name='edit'))

    if form.submitted(request):
        self.accept(request)
        request.message(_("Press release accepted."), 'success')
        return redirect(layout.dashboard_or_press_releases_link)

    return {
        'message': _(
            'Do you really want to accept "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Accept Press Release"),
        'button_text': _("Accept Press Release"),
        'cancel': request.link(self)
    }


@GazetteApp.form(
    model=PressRelease,
    name='reject',
    template='form.pt',
    permission=Private,
    form=RejectForm
)
def reject_press_release(self, request, form):
    """ Reject a press release.

    This view is used by the publishers to reject a submitted press release.

    Only submitted press releases may be rejected.

    """

    layout = Layout(self, request)

    if self.state != 'submitted':
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Reject Press Release"),
            'callout': _("Only submitted press releases may be rejected."),
            'show_form': False
        }

    if form.submitted(request):
        self.reject(request, form.comment.data)
        request.message(_("Press release rejected."), 'success')
        return redirect(layout.dashboard_or_press_releases_link)

    return {
        'message': _(
            'Do you really want to reject "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Reject Press Release"),
        'button_text': _("Reject Press Release"),
        'button_class': 'alert',
        'cancel': request.link(self)
    }


@GazetteApp.form(
    model=PressRelease,
    name='publish',
    template='form.pt',
    permission=Private,
    form=PublishPressReleaseForm
)
def publish_press_release(self, request, form):
    """ Publish a press release.

    This view is used by the publishers to publish an accepted press release.

    Only accepted press releases may be accepted.

    """

    layout = Layout(self, request)

    if self.state != 'accepted':
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Publish Press Release"),
            'callout': _("Only accepted press releases may be published."),
            'show_form': False
        }

    if self.invalid_organization:
        return redirect(request.link(self, name='edit'))

    if form.submitted(request):
        self.publish(request)
        request.message(_("Press release published."), 'success')
        return redirect(layout.dashboard_or_press_releases_link)

    return {
        'message': _(
            'Do you really want to publish "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Publish Press Release"),
        'button_text': _("Publish Press Release"),
        'cancel': request.link(self)
    }
