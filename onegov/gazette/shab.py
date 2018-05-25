from dateutil.parser import parse
from lxml import etree
from onegov.chat import MessageCollection
from onegov.gazette import _
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Issue
from onegov.notice.collections import get_unique_notice_name
from requests import get
from requests import post
from textwrap import dedent
from uuid import uuid4
from onegov.gazette import log


class ShabConverter(object):
    def __init__(self, root):
        self.root = root

    def get(self, path, converter=None):
        result = self.root.find(path)
        result = result.text.strip() if result is not None else result
        result = result.replace('\n', '<br>') if result else result
        result = converter(result) if converter and result else result
        return result or ''

    @property
    def title(self):
        return self.get('meta/title/de')

    @property
    def source(self):
        return self.get('meta/publicationNumber')

    @property
    def organization_id(self):
        return '308'

    @property
    def category_id(self):
        return '9'

    @property
    def date(self):
        return self.get('meta/publicationDate', converter=parse)

    def issues(self, session):
        query = session.query(Issue.name)
        query = query.filter(Issue.date > self.date)
        query = query.order_by(Issue.date)
        query = query.first()
        return [query.name] if query else []


class KK01(ShabConverter):

    @property
    def text(self):
        return dedent(f"""
        <p><strong>Schuldner</strong><br>
        {self.get('content/debtor/companies/company/name')}<br>
        {self.get('content/debtor/companies/company/address/street')}<br>
        {self.get('content/debtor/companies/company/address/swissZipCode')}
         {self.get('content/debtor/companies/company/address/town')}</p>
        <p><strong>Angaben zur vorläufigen Konkursanzeige</strong></p>
        <p><strong>Datum der Konkurseröffnung</strong><br>
        {self.get('content/resolutionDate', parse):%d.%m.%Y}</p>
        <p><strong>Rechtliche Hinweise und Fristen</strong><br>
        {self.get('meta/legalRemedy')}</p>
        <p><strong>Ergänzende rechtliche Hinweise</strong><br>
        {self.get('content/additionalLegalRemedy')}</p>
        <p><strong>Weitere Angaben zur Meldung</strong><br>
        {self.get('content/remarks')}</p>
        """).strip().replace('\n', '')


class KK02(ShabConverter):

    @property
    def text(self):
        return dedent(f"""
        <p><strong>Schuldner</strong><br>
        {self.get('content/debtor/companies/company/name')}<br>
        {self.get('content/debtor/companies/company/address/street')}<br>
        {self.get('content/debtor/companies/company/address/swissZipCode')}
         {self.get('content/debtor/companies/company/address/town')}</p>
        <p><strong>Angaben zur Konkursmeldung/Schuldenruf</strong></p>
        <p><strong>Art des Konkursverfahrens</strong><br>
        {self.get('content/proceeding/selectType')}</p>
        <p><strong>Frist</strong><br>
        {self.get('content/daysAfterPublication', int)} Tage</p>
        <p><strong>Ablauf der Frist</strong><br>
        {self.get('content/entryDeadline', parse):%d.%m.%Y}</p>
        <p><strong>Kommentar zur Frist</strong><br>
        {self.get('content/commentEntryDeadline')}</p>
        <p><strong>Anmeldestelle</strong><br>
        {self.get('content/registrationOffice')}</p>
        <p><strong>Datum der Konkurseröffnung</strong><br>
        {self.get('content/resolutionDate', parse):%d.%m.%Y}</p>
        <p><strong>Rechtliche Hinweise und Fristen</strong><br>
        {self.get('meta/legalRemedy')}</p>
        <p><strong>Ergänzende rechtliche Hinweise</strong><br>
        {self.get('content/additionalLegalRemedy')}</p>
        <p><strong>Weitere Angaben zur Meldung</strong><br>
        {self.get('content/remarks')}</p>
        """).strip().replace('\n', '')


class KK03(ShabConverter):

    @property
    def text(self):
        return dedent(f"""
        <p><strong>Schuldner</strong><br>
        {self.get('content/debtor/companies/company/name')}<br>
        {self.get('content/debtor/companies/company/address/street')}<br>
        {self.get('content/debtor/companies/company/address/swissZipCode')}
         {self.get('content/debtor/companies/company/address/town')}</p>
        <p><strong>Angaben zur Einstellung des Konkursverfahrens</strong></p>
        <p><strong>Datum der Konkurseröffnung</strong><br>
        {self.get('content/resolutionDate', parse):%d.%m.%Y}</p>
        <p><strong>Datum der Einstellung</strong><br>
        {self.get('content/cessationDate', parse):%d.%m.%Y}</p>
        <p><strong>Betrag des Kostenvorschusses</strong><br>
        {self.get('content/advanceAmount', float)} CHF</p>
        <p><strong>Rechtliche Hinweise und Fristen</strong><br>
        {self.get('meta/legalRemedy')}</p>
        <p><strong>Frist</strong><br>
        {self.get('content/daysAfterPublication', int)} Tage</p>
        <p><strong>Ablauf der Frist</strong><br>
        {self.get('content/entryDeadline', parse):%d.%m.%Y}</p>
        <p><strong>Kommentar zur Frist</strong><br>
        {self.get('content/commentEntryDeadline')}</p>
        <p><strong>Anmeldestelle</strong><br>
        {self.get('content/registrationOffice')}</p>
        <p><strong>Ergänzende rechtliche Hinweise</strong><br>
        {self.get('content/additionalLegalRemedy')}</p>
        <p><strong>Weitere Angaben zur Meldung</strong><br>
        {self.get('content/remarks')}</p>
        """).strip().replace('\n', '')


class ShabImporter(object):

    def __init__(
        self, session,
        endpoint, username, password, canton, rubrics, subrubrics
    ):
        self.session = session
        self.endpoint = endpoint.rstrip('/')
        self.username = username
        self.password = password
        self.canton = canton
        self.rubrics = rubrics
        self.subrubrics = subrubrics
        self.token = None
        self.converters = {
            'KK01': KK01,
            'KK02': KK02,
            'KK03': KK03
        }

    def login(self):
        """ Login to the service and store the token. The token will be valid
        for half an hour.

        """
        response = post(
            f'{self.endpoint}/login',
            data={'username': self.username, 'password': self.password}
        )
        response.raise_for_status()
        self.token = response.headers['x-auth-token']

    def get_publication_ids(self):
        """ Returns the IDs of the publications we are interested in. Does not
        include the IDs of the publications which has been already imported
        previously.

        """
        result = {}

        page = 0
        while page is not None:
            response = get(
                f'{self.endpoint}/publications/xml',
                params={
                    'publicationStates': 'PUBLISHED',
                    'cantons': self.canton,
                    'rubrics': self.rubrics,
                    'subRubrics': self.subrubrics,
                    'pageRequest.page': page,
                    'pageRequest.size': 2000,
                },
                headers={'X-AUTH-TOKEN': self.token}
            )
            response.raise_for_status()

            root = etree.fromstring(response.text.encode('utf-8'))
            publications = {
                meta.find('publicationNumber').text: meta.find('id').text
                for meta in root.findall('publication/meta')
            }

            result.update(publications)
            page = page + 1 if publications else None

        existing = self.session.query(GazetteNotice.source)
        existing = existing.filter(GazetteNotice.source.isnot(None))
        existing = set([result.source for result in existing])

        return [
            id_ for source, id_ in result.items() if source not in existing
        ]

    def get_publication(self, identifier):
        """ Fetches a single publication and adds it as an official notice.

        """
        response = get(
            f'{self.endpoint}/publications/{identifier}/xml',
            headers={'X-AUTH-TOKEN': self.token}
        )
        response.raise_for_status()

        root = etree.fromstring(response.text.encode('utf-8'))
        subrubric = root.find('meta/subRubric').text
        id_ = uuid4()
        try:
            converter = self.converters[subrubric](root)
            notice = GazetteNotice(
                id=id_,
                name=get_unique_notice_name(
                    converter.title, self.session, GazetteNotice
                ),
                state='imported',
                source=converter.source,
                title=converter.title,
                text=converter.text,
                issues=converter.issues(self.session)
            )
            notice.organization_id = converter.organization_id
            notice.category_id = converter.category_id
        except ValueError:
            log.error(f'Could not import SHAB notice {identifier}')
        else:
            notice.apply_meta(self.session)
            self.session.add(notice)
            self.session.flush()
            MessageCollection(self.session, type='gazette_notice').add(
                channel_id=str(notice.id),
                meta={'event': _("imported")}
            )

    def __call__(self, clear=False):
        if clear:
            existing = self.session.query(GazetteNotice)
            existing = existing.filter(GazetteNotice.source.isnot(None))
            existing.delete()

        self.login()
        for id_ in self.get_publication_ids():
            self.get_publication(id_)
