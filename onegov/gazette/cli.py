""" Provides commands used to initialize gazette websites. """

import click
import transaction

from datetime import timedelta
from dateutil import parser
from json import loads
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.core.crypto import random_password
from onegov.core.csv import convert_xls_to_csv
from onegov.core.csv import CSVFile
from onegov.core.templates import render_template
from onegov.gazette import _
from onegov.gazette.collections import CategoryCollection
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.collections import IssueCollection
from onegov.gazette.collections import OrganizationCollection
from onegov.gazette.collections import PublishedNoticeCollection
from onegov.gazette.collections import SubscriptionCollection
from onegov.gazette.layout import MailLayout
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import GazetteSubscription
from onegov.gazette.models import IssueName
from onegov.user import User
from onegov.user import UserCollection
from onegov.user import UserGroupCollection
from sedate import standardize_date
from sedate import utcnow

cli = command_group()


@cli.command(context_settings={'creates_path': True})
@pass_group_context
def add(group_context):
    """ Adds a gazette instance to the database. For example:

        onegov-gazette --select '/onegov_gazette/zug' add

    """

    def add_instance(request, app):
        if not app.principal:
            click.secho("principal.yml not found", fg='yellow')
        click.echo("Instance was created successfully")

    return add_instance


@cli.command(name='import-editors')
@click.argument('file', type=click.File('rb'))
@click.option('--clear/--no-clear', default=False)
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--locale', default='de_CH')
@pass_group_context
def import_editors(ctx, file, clear, dry_run, locale):
    """ Imports editors and groups. For example:

        onegov-gazette --select '/onegov_gazette/zug' import-editors data.xlsx

    """

    def import_editors_and_groups(request, app):
        request.locale = locale
        headers = {
            'group': request.translate(_("Group")),
            'name': request.translate(_("Name")),
            'email': request.translate(_("E-Mail"))
        }

        session = app.session()
        users = UserCollection(session)
        groups = UserGroupCollection(session)

        if clear:
            click.secho("Deleting all editors", fg='yellow')
            for user in users.query().filter(User.role == 'member'):
                session.delete(user)

            click.secho("Deleting all groups", fg='yellow')
            for group in groups.query():
                session.delete(group)

        csvfile = convert_xls_to_csv(
            file, sheet_name=request.translate(_("Editors"))
        )
        csv = CSVFile(csvfile, expected_headers=headers.values())
        lines = list(csv.lines)
        columns = {
            key: csv.as_valid_identifier(value)
            for key, value in headers.items()
        }

        added_groups = {}
        for group in set([line.gruppe for line in lines]):
            added_groups[group] = groups.add(name=group)
        click.secho(
            "{} group(s) imported".format(len(added_groups)), fg='green'
        )

        count = 0
        for line in lines:
            count += 1
            email = getattr(line, columns['email'])
            realname = getattr(line, columns['name'])
            group = getattr(line, columns['group'])
            group = added_groups[group] if group else None
            users.add(
                username=email,
                realname=realname,
                group=group,
                password=random_password(),
                role='member',
            )

        click.secho("{} editor(s) imported".format(count), fg='green')

        if dry_run:
            transaction.abort()

    return import_editors_and_groups


@cli.command(name='import-organizations')
@click.argument('file', type=click.File('rb'))
@click.option('--clear/--no-clear', default=False)
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--locale', default='de_CH')
@pass_group_context
def import_organizations(ctx, file, clear, dry_run, locale):
    """ Imports Organizations. For example:

        onegov-gazette --select '/onegov_gazette/zug' \
            import-organizations data.xlsx

    """

    def _import_organizations(request, app):
        request.locale = locale
        headers = {
            'id': request.translate(_("ID")),
            'name': request.translate(_("Name")),
            'title': request.translate(_("Title")),
            'active': request.translate(_("Active")),
            'parent': request.translate(_("Parent Organization"))
        }

        session = app.session()
        organizations = OrganizationCollection(session)

        if clear:
            click.secho("Deleting organizations", fg='yellow')
            for organization in organizations.query():
                session.delete(organization)

        csvfile = convert_xls_to_csv(
            file, sheet_name=request.translate(_("Organizations"))
        )
        csv = CSVFile(csvfile, expected_headers=headers.values())
        lines = list(csv.lines)
        columns = {
            key: csv.as_valid_identifier(value)
            for key, value in headers.items()
        }

        count = 0
        for line in lines:
            count += 1
            id_ = int(getattr(line, columns['id']))
            name = getattr(line, columns['name'])
            parent = getattr(line, columns['parent'])
            parent = int(parent) if parent else None
            title = getattr(line, columns['title'])
            active = bool(int(getattr(line, columns['active'])))

            organization = organizations.add_root(
                id=id_,
                name=name,
                title=title,
                active=active,
                order=count
            )
            organization.parent_id = parent

        click.secho("{} organization(s) imported".format(count), fg='green')

        if dry_run:
            transaction.abort()

    return _import_organizations


@cli.command(name='import-categories')
@click.argument('file', type=click.File('rb'))
@click.option('--clear/--no-clear', default=False)
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--locale', default='de_CH')
@pass_group_context
def import_categories(ctx, file, clear, dry_run, locale):
    """ Imports categories. For example:

        onegov-gazette --select '/onegov_gazette/zug' \
            import-categories data.xlsx

    """

    def _import_categories(request, app):

        request.locale = locale
        headers = {
            'id': request.translate(_("ID")),
            'name': request.translate(_("Name")),
            'title': request.translate(_("Title")),
            'active': request.translate(_("Active"))
        }

        session = app.session()
        categories = CategoryCollection(session)

        if clear:
            click.secho("Deleting categories", fg='yellow')
            for category in categories.query():
                session.delete(category)

        csvfile = convert_xls_to_csv(
            file, sheet_name=request.translate(_("Categories"))
        )
        csv = CSVFile(csvfile, expected_headers=headers.values())
        lines = list(csv.lines)
        columns = {
            key: csv.as_valid_identifier(value)
            for key, value in headers.items()
        }

        count = 0
        for line in lines:
            count += 1
            id_ = int(getattr(line, columns['id']))
            name = getattr(line, columns['name'])
            title = getattr(line, columns['title'])
            active = bool(int(getattr(line, columns['active'])))
            categories.add_root(
                id=id_,
                name=name,
                title=title,
                active=active,
                order=count
            )

        click.secho("{} categorie(s) imported".format(count), fg='green')

        if dry_run:
            transaction.abort()

    return _import_categories


@cli.command(name='import-issues')
@click.argument('file', type=click.File('rb'))
@click.option('--clear/--no-clear', default=False)
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--locale', default='de_CH')
@click.option('--timezone', default=None)
@pass_group_context
def import_issues(ctx, file, clear, dry_run, locale, timezone):
    """ Imports issues. For example:

        onegov-gazette --select '/onegov_gazette/zug' import-issues data.xlsx

    """

    def _import_issues(request, app):
        request.locale = locale
        headers = {
            'number': request.translate(_("Number")),
            'date': request.translate(_("Date")),
            'deadline': request.translate(_("Deadline"))
        }

        session = app.session()
        issues = IssueCollection(session)

        if clear:
            click.secho("Deleting issues", fg='yellow')
            for category in issues.query():
                session.delete(category)

        csvfile = convert_xls_to_csv(
            file, sheet_name=request.translate(_("Issues"))
        )
        csv = CSVFile(csvfile, expected_headers=headers.values())
        lines = list(csv.lines)
        columns = {
            key: csv.as_valid_identifier(value)
            for key, value in headers.items()
        }

        count = 0
        for line in lines:
            count += 1
            number = int(getattr(line, columns['number']))
            date_ = parser.parse(getattr(line, columns['date'])).date()
            deadline = standardize_date(
                parser.parse(getattr(line, columns['deadline'])),
                timezone or request.app.principal.time_zone
            )
            name = str(IssueName(date_.year, number))

            issues.add(
                name=name,
                number=number,
                date=date_,
                deadline=deadline
            )

        click.secho("{} categorie(s) imported".format(count), fg='green')

        if dry_run:
            transaction.abort()

    return _import_issues


@cli.command(name='import-notices')
@click.argument('file', type=click.File('rb'))
@click.option('--clear/--no-clear', default=False)
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--locale', default='de_CH')
@click.option('--timezone', default=None)
@pass_group_context
def import_notices(ctx, file, clear, dry_run, locale, timezone):
    """ Imports issues. For example:

        onegov-gazette --select '/onegov_gazette/zug' import-notices data.xlsx

    """

    def _import_notices(request, app):
        request.locale = locale
        headers = {
            'name': request.translate(_("Name")),
            'state': request.translate(_("State")),
            'source': request.translate(_("Source")),
            'title': request.translate(_("Title")),
            'text': request.translate(_("Text")),
            'author_date': request.translate(_("Author Place")),
            'author_name': request.translate(_("Author Date")),
            'author_place': request.translate(_("Author Name")),
            'issues': request.translate(_("Issues")),
            'expiry_date': request.translate(_("Expiry Date")),
            'category_id': request.translate(_("Category")),
            'organization_id': request.translate(_("Organization")),
            'print_only': request.translate(_("Print only")),
            'at_cost': request.translate(_("Liable to pay costs")),
            'billing_address': request.translate(_("Billing address")),
        }

        session = app.session()
        notices = GazetteNoticeCollection(session)

        if clear:
            click.secho("Deleting notices", fg='yellow')
            for category in notices.query():
                session.delete(category)

        csvfile = convert_xls_to_csv(
            file, sheet_name=request.translate(_("Official Notices"))
        )
        csv = CSVFile(csvfile, expected_headers=headers.values())
        lines = list(csv.lines)
        columns = {
            key: csv.as_valid_identifier(value)
            for key, value in headers.items()
        }

        count = 0
        for line in lines:
            count += 1
            name = getattr(line, columns['name'])
            state = getattr(line, columns['state'])
            source = getattr(line, columns['source']) or None
            title = getattr(line, columns['title'])
            text = getattr(line, columns['text'])
            author_date = getattr(line, columns['author_date']) or None
            if author_date:
                author_date = standardize_date(
                    parser.parse(author_date),
                    timezone or request.app.principal.time_zone
                )
            author_name = getattr(line, columns['author_name'])
            author_place = getattr(line, columns['author_place'])
            issues = loads(getattr(line, columns['issues']))
            expiry_date = getattr(line, columns['expiry_date']) or None
            if expiry_date:
                expiry_date = standardize_date(
                    parser.parse(expiry_date),
                    timezone or request.app.principal.time_zone
                )
            category_id = getattr(line, columns['category_id'])
            organization_id = getattr(line, columns['organization_id'])
            print_only = bool(int(getattr(line, columns['print_only'])))
            at_cost = bool(int(getattr(line, columns['at_cost'])))
            billing_address = getattr(line, columns['billing_address'])
            notice = GazetteNotice(
                name=name,
                state=state,
                source=source,
                title=title,
                text=text,
                author_date=author_date,
                author_name=author_name,
                author_place=author_place,
                issues=issues,
                expiry_date=expiry_date,
                category_id=category_id,
                organization_id=organization_id,
                print_only=print_only,
                at_cost=at_cost,
                billing_address=billing_address
            )
            notice.apply_meta(session)
            session.add(notice)

        click.secho("{} notice(s) imported".format(count), fg='green')

        if dry_run:
            transaction.abort()

    return _import_notices


@cli.command(name='process-subscriptions')
@pass_group_context
def process_subscriptions(ctx):
    """ Imports issues. For example:

        onegov-gazette --select '/onegov_gazette/zug' import-issues data.xlsx

    """

    def _process_subscriptions(request, app):
        session = app.session()
        query = SubscriptionCollection(session).query()
        query = query.filter(GazetteSubscription.validated.is_(True))
        for subscription in query:
            request.locale = subscription.locale
            notices = PublishedNoticeCollection(
                session,
                term=subscription.term,
                order=subscription.order,
                direction=subscription.direction,
                categories=subscription.categories,
                organizations=subscription.organizations,
                from_date=subscription.last_sent.date(),
                to_date=utcnow().date() + timedelta(days=1)
            )
            if notices.query().first():
                request.app.send_marketing_email(
                    subject=_("New official notices"),
                    receivers=(subscription.email, ),
                    reply_to=request.app.mail['marketing']['sender'],
                    content=render_template(
                        'mail_subscription.pt',
                        request,
                        {
                            'title': _("New official notices"),
                            'layout': MailLayout(subscription, request),
                            'url': request.link(notices)
                        }
                    )
                )

            subscription.last_sent = utcnow()

    return _process_subscriptions
