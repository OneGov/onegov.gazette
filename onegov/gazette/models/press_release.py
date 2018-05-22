from onegov.gazette.models.notice import GazetteNoticeBase
from onegov.gazette.models.organization import Organization


class PressRelease(GazetteNoticeBase):
    """ A press release. """

    __mapper_args__ = {'polymorphic_identity': 'press_release'}

    @property
    def issue_date(self):
        return self.first_issue

    @issue_date.setter
    def issue_date(self, value):
        self.first_issue = value

    def apply_meta(self, session):
        """ Updates the organization. """
        self.organization = None
        query = session.query(Organization.title)
        query = query.filter(Organization.name == self.organization_id).first()
        if query:
            self.organization = query[0]
