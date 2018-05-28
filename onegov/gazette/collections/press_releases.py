from onegov.chat import MessageCollection
from onegov.gazette import _
from onegov.gazette.collections.notices import GazetteNoticeCollection
from onegov.gazette.models import PressRelease
from sedate import standardize_date
from uuid import uuid4


class PressReleaseCollection(GazetteNoticeCollection):
    """ Manage a list of press releases. """

    @property
    def model_class(self):
        return PressRelease

    def add(self, title, text, organization_id, user, issue_date, timezone,
            blocking_period, **kwargs):
        """ Add a new press release.

        A unique, URL-friendly name is created automatically for this press
        release using the title and optionally numbers for duplicate names.

        A entry is added automatically to the audit trail.

        Returns the created press release.
        """

        press_release = PressRelease(
            id=uuid4(),
            state='drafted',
            title=title,
            text=text,
            name=self._get_unique_name(title),
            **kwargs
        )
        press_release.issue_date = standardize_date(issue_date, timezone)
        if blocking_period:
            press_release.blocking_period = standardize_date(
                blocking_period, timezone
            )
        press_release.user = user
        press_release.group = user.group if user else None
        press_release.organization_id = organization_id
        press_release.apply_meta(self.session)
        self.session.add(press_release)
        self.session.flush()

        audit_trail = MessageCollection(self.session, type='press_release')
        audit_trail.add(
            channel_id=str(press_release.id),
            owner=str(user.id) if user else '',
            meta={'event': _("created")}
        )

        return press_release


class PublishedPressReleaseCollection(PressReleaseCollection):

    def __init__(self, session, **kwargs):
        kwargs.pop('state', None)
        super(PublishedPressReleaseCollection, self).__init__(
            session,
            state='published',
            **kwargs
        )
