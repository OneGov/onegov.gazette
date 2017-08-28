from datetime import date
from datetime import datetime
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.models import Principal
from onegov.user import UserCollection
from onegov.user import UserGroupCollection
from sedate import standardize_date


class DummyApp(object):
    def __init__(self, principal):
        self.principal = principal


class DummyRequest(object):
    def __init__(self, principal):
        self.app = DummyApp(principal)


def test_notice_collection(session, principal):
    user = UserCollection(session).add(
        username='a@a.a', password='a', role='admin'
    )

    collection = GazetteNoticeCollection(session)
    collection.add(
        title='Notice A',
        text='An <strong>important</strong> Notice!',
        organization_id='100',
        category_id='11',
        issues=['2017-46', '2017-47'],
        user=user,
        principal=principal
    )
    collection.add(
        title='Notice B',
        text='Another Notice',
        organization_id='200',
        category_id='13',
        issues={'2017-47', '2017-48'},
        user=user,
        principal=principal
    )

    notice = collection.query().filter_by(title='Notice A').one()
    assert notice.title == 'Notice A'
    assert notice.text == 'An <strong>important</strong> Notice!'
    assert notice.organization_id == '100'
    assert notice.organization == 'State Chancellery'
    assert notice.category_id == '11'
    assert notice.category == 'Education'
    assert notice.issues == {'2017-46': None, '2017-47': None}
    assert notice.first_issue == standardize_date(
        datetime(2017, 11, 17), 'Europe/Zurich'
    )
    assert notice.user == user
    assert notice.changes.one().event == 'created'
    assert notice.changes.one().user == user

    notice = collection.query().filter_by(title='Notice B').one()
    assert notice.title == 'Notice B'
    assert notice.text == 'Another Notice'
    assert notice.organization_id == '200'
    assert notice.organization == 'Civic Community'
    assert notice.category_id == '13'
    assert notice.category == 'Commercial Register'
    assert notice.issues == {'2017-47': None, '2017-48': None}
    assert notice.first_issue == standardize_date(
        datetime(2017, 11, 24), 'Europe/Zurich'
    )
    assert notice.user == user
    assert notice.changes.one().event == 'created'
    assert notice.changes.one().user == user


def test_notice_collection_on_request(session, principal):
    collection = GazetteNoticeCollection(session)
    assert collection.from_date is None
    assert collection.to_date is None
    assert collection.issues is None

    collection.on_request(DummyRequest(principal))
    assert collection.issues is None

    for start, end, length in (
        (date(2015, 1, 1), date(2020, 1, 1), 14),
        (None, date(2020, 1, 1), 14),
        (date(2015, 1, 1), None, 14),
        (date(2017, 10, 14), date(2017, 11, 18), 5),
        (None, date(2017, 11, 18), 7),
        (date(2017, 10, 14), None, 12),
        (date(2017, 10, 20), date(2017, 10, 20), 1),
        (date(2017, 10, 21), date(2017, 10, 21), 0),
        (date(2017, 10, 1), date(2017, 9, 1), 0),
    ):
        collection = collection.for_dates(start, end)
        collection.on_request(DummyRequest(principal))
        assert len(collection.issues) == length

    collection = collection.for_dates(date(2017, 12, 1), date(2017, 12, 10))
    collection.on_request(DummyRequest(principal))
    assert sorted(collection.issues) == ['2017-48', '2017-49']


def test_notice_collection_count_by_organization(session):
    collection = GazetteNoticeCollection(session)
    assert collection.count_by_organization() == []

    principal = Principal(organizations=[{'1': 'A'}, {'2': 'B'}, {'3': 'C'}])
    for organization, count in (('1', 2), ('2', 4), ('3', 10)):
        for x in range(count):
            collection.add(
                title='',
                text='',
                organization_id=organization,
                category_id='',
                issues=['2017-{}'.format(y) for y in range(x)],
                user=None,
                principal=principal
            )
    # for x in collection.query(): x.organization, x.issues

    assert collection.count_by_organization() == [
        ('A', 1), ('B', 6), ('C', 45),
    ]

    assert collection.count_by_organization() == \
        collection.for_state('drafted').count_by_organization()

    collection.issues = ['2017-1', '2017-4']
    assert collection.count_by_organization() == [('B', 2), ('C', 13)]


def test_notice_collection_count_by_category(session):
    collection = GazetteNoticeCollection(session)
    assert collection.count_by_category() == []

    principal = Principal(categories=[{'1': 'A'}, {'2': 'B'}, {'3': 'C'}])
    for category, count in (('1', 2), ('2', 4), ('3', 1)):
        for x in range(count):
            collection.add(
                title='',
                text='',
                organization_id=None,
                category_id=category,
                issues=['2017-{}'.format(y) for y in range(x)],
                user=None,
                principal=principal
            )
    assert collection.count_by_category() == [('A', 1), ('B', 6)]

    assert collection.count_by_category() == \
        collection.for_state('drafted').count_by_category()

    collection.issues = ['2017-0', '2017-2']
    assert collection.count_by_category() == [('A', 1), ('B', 4)]


def test_notice_collection_count_by_group(session, principal):
    collection = GazetteNoticeCollection(session)
    assert collection.count_by_group() == []

    groups = UserGroupCollection(session)
    group_a = groups.add(name='A')
    group_b = groups.add(name='B')
    groups.add(name='C')

    users = UserCollection(session)
    user_a = users.add('a@example.org', 'pw', 'editor', group=group_a)
    user_b = users.add('b@example.org', 'pw', 'editor', group=group_a)
    user_c = users.add('c@example.org', 'pw', 'admin')
    user_d = users.add('d@example.org', 'pw', 'publisher')
    user_e = users.add('e@example.org', 'pw', 'publisher', group=group_b)
    user_f = users.add('f@example.org', 'pw', 'publisher')
    user_g = users.add('g@example.org', 'pw', 'publisher')
    user_h = users.add('h@example.org', 'pw', 'publisher')

    for user, count in (
        (user_a, 2),
        (user_b, 4),
        (user_c, 1),
        (user_d, 7),
        (user_e, 2),
        (user_f, 3),
        (user_g, 6),
        (user_h, 2),
    ):
        for x in range(count):
            collection.add(
                title='',
                text='',
                organization_id='',
                category_id='',
                issues=['2017-{}'.format(y) for y in range(x)],
                user=user,
                principal=principal
            )
    assert collection.count_by_group() == [
        ('A', 7), ('B', 1)
    ]

    assert collection.count_by_group() == \
        collection.for_state('drafted').count_by_group()

    collection.issues = ['2017-2', '2017-4']
    assert collection.count_by_group() == [
        ('A', 1)
    ]
