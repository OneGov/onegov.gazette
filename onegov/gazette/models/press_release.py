from dateutil.parser import parse
from onegov.core.orm.mixins import meta_property
from onegov.gazette.models.notice import GazetteNoticeBase
from onegov.gazette.models.organization import Organization
from sedate import utcnow


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

    #: The Blocking period of the press release.
    blocking_period = meta_property('blocking_period')

    @blocking_period.setter
    def set_blocking_period(self, value):
        self.meta['blocking_period'] = value.isoformat() if value else value

    @blocking_period.getter
    def get_blocking_period(self):
        value = (self.meta or {}).get('blocking_period', None)
        if value:
            return parse(value)
        return value

    @property
    def blocked(self):
        return self.blocking_period and self.blocking_period > utcnow()

    #: The contact responsible for the press release content.
    contact = meta_property('contact')

    #: The press conference related to this press release.
    conference = meta_property('conference')

    #: The lead.
    lead = meta_property('lead')
