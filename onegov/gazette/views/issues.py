from morepath import redirect
from onegov.core.security import Secret
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import IssueCollection
from onegov.gazette.forms import IssueForm
from onegov.gazette.forms import EmptyForm
from onegov.gazette.layout import Layout
from onegov.gazette.models import Issue


@GazetteApp.html(
    model=IssueCollection,
    template='issues.pt',
    permission=Secret
)
def view_issues(self, request):
    """ View the list of issues.

    This view is only visible by an admin.

    """
    layout = Layout(self, request)

    return {
        'layout': layout,
        'issues': self.query().all(),
        'new_issue': request.link(self, name='new-issue')
    }


@GazetteApp.form(
    model=IssueCollection,
    name='new-issue',
    template='form.pt',
    permission=Secret,
    form=IssueForm
)
def create_issue(self, request, form):
    """ Create a new issue.

    This view is only visible by an admin.

    """
    layout = Layout(self, request)

    if form.submitted(request):
        issue = Issue()
        form.update_model(issue)
        request.app.session().add(issue)
        request.message(_("Issue added."), 'success')
        return redirect(layout.manage_issues_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("New Issue"),
        'button_text': _("Save"),
        'cancel': layout.manage_issues_link
    }


@GazetteApp.form(
    model=Issue,
    name='edit',
    template='form.pt',
    permission=Secret,
    form=IssueForm
)
def edit_issue(self, request, form):
    """ Edit a issue.

    This view is only visible by an admin.

    """

    layout = Layout(self, request)
    if form.submitted(request):
        form.update_model(self)
        request.message(_("Issue modified."), 'success')
        return redirect(layout.manage_issues_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.name,
        'subtitle': _("Edit Issue"),
        'button_text': _("Save"),
        'cancel': layout.manage_issues_link,
    }


@GazetteApp.form(
    model=Issue,
    name='delete',
    template='form.pt',
    permission=Secret,
    form=EmptyForm
)
def delete_issue(self, request, form):
    """ Delete a issue.

    Only unused issues may be deleted.

    """
    layout = Layout(self, request)
    session = request.app.session()

    if self.in_use(session):
        request.message(
            _("Only unused issues may be deleted."),
            'alert'
        )
        return {
            'layout': layout,
            'title': self.name,
            'subtitle': _("Delete Issue"),
            'show_form': False
        }

    if form.submitted(request):
        collection = IssueCollection(session)
        collection.delete(self)
        request.message(_("Issue deleted."), 'success')
        return redirect(layout.manage_issues_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.name}
        ),
        'layout': layout,
        'form': form,
        'title': self.name,
        'subtitle': _("Delete Issue"),
        'button_text': _("Delete Issue"),
        'button_class': 'alert',
        'cancel': layout.manage_issues_link
    }