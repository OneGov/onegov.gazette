from datetime import datetime
from email.utils import format_datetime
from io import BytesIO
from morepath import redirect
from morepath.request import Response
from onegov.core.security import Public
from onegov.core.templates import render_template
from onegov.core.utils import normalize_for_url
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import CategoryCollection
from onegov.gazette.collections import OrganizationCollection
from onegov.gazette.collections import PublishedNoticeCollection
from onegov.gazette.collections import SubscriptionCollection
from onegov.gazette.forms import SubscriptionConfirmationForm
from onegov.gazette.forms import SubscriptionForm
from onegov.gazette.layout import Layout
from onegov.gazette.layout import MailLayout
from onegov.gazette.pdf import Pdf
from sedate import utcnow
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import SubElement


def send_confirmation_mail(request, subscription):
    """ Sends a mail to a new subscriber with a link to activate the
    subscription.

    """

    url = '{}?token={}'.format(
        request.link(
            SubscriptionCollection(request.session),
            name='confirm-subscription'
        ).rstrip('/'),
        request.new_url_safe_token({'email': subscription.email})
    )

    subject = _("Confirm your subscription")
    content = render_template(
        'mail_confirm_subscription.pt',
        request,
        {
            'title': subject,
            'layout': MailLayout(subscription, request),
            'url': url
        }
    )

    request.app.send_transactional_email(
        subject=subject,
        receivers=(subscription.email, ),
        reply_to=request.app.mail['transactional']['sender'],
        content=content
    )


@GazetteApp.html(
    model=PublishedNoticeCollection,
    template='notices_search.pt',
    permission=Public
)
def view_published_notices(self, request):
    """ Search the published notices. """

    layout = Layout(self, request)
    session = request.session

    orderings = {
        'first_issue': {
            'title': _("Issue(s)"),
            'href': request.link(self.for_order('first_issue')),
            'sort': self.direction if self.order == 'first_issue' else '',
        },
        'organization': {
            'title': _("Organization"),
            'href': request.link(self.for_order('organization')),
            'sort': self.direction if self.order == 'organization' else '',
        },
        'category': {
            'title': _("Category"),
            'href': request.link(self.for_order('category')),
            'sort': self.direction if self.order == 'category' else '',
        },
        'title': {
            'title': _("Title"),
            'href': request.link(self.for_order('title')),
            'sort': self.direction if self.order == 'title' else '',
        },
    }

    clear = None
    if any((
        self.term, self.categories, self.organizations,
        self.from_date, self.to_date
    )):
        target = self.for_dates(None, None)
        target = target.for_term(None)
        target = target.for_organizations(None)
        target = target.for_categories(None)
        clear = request.link(target)

    return {
        'layout': layout,
        'notices': self.batch,
        'term': self.term,
        'categories': CategoryCollection(session).as_options(),
        'organizations': OrganizationCollection(session).as_options(
            grouped=True
        ),
        'selected_categories': self.categories,
        'selected_organizations': self.organizations,
        'from_date': self.from_date,
        'to_date': self.to_date,
        'import_source': self.import_source,
        'orderings': orderings,
        'clear': clear,
        'pdf': request.link(self, name='pdf'),
        'subscribe': request.link(self, name='subscribe')
    }


@GazetteApp.html(
    model=PublishedNoticeCollection,
    template='notices_embed.pt',
    name='embed',
    permission=Public
)
def view_published_notices_embed(self, request):
    """ Show the search results embeddable. """

    layout = Layout(self, request)

    orderings = {
        'first_issue': {
            'title': _("Issue(s)"),
            'href': request.link(self.for_order('first_issue')),
            'sort': self.direction if self.order == 'first_issue' else '',
        },
        'organization': {
            'title': _("Organization"),
            'href': request.link(self.for_order('organization')),
            'sort': self.direction if self.order == 'organization' else '',
        },
        'category': {
            'title': _("Category"),
            'href': request.link(self.for_order('category')),
            'sort': self.direction if self.order == 'category' else '',
        },
        'title': {
            'title': _("Title"),
            'href': request.link(self.for_order('title')),
            'sort': self.direction if self.order == 'title' else '',
        },
    }

    return {
        'layout': layout,
        'notices': self.batch,
        'term': self.term,
        'orderings': orderings,
    }


@GazetteApp.view(
    model=PublishedNoticeCollection,
    name='rss',
    permission=Public
)
def view_published_notices_rss(self, request):
    """ Show the search results as RSS feed. """

    def sub(parent, tag, text=None, attrib=None):
        element = SubElement(parent, tag, attrib=attrib or {})
        element.text = text or ''
        return element

    @request.after
    def set_headers(response):
        response.headers['Content-Type'] = 'application/rss+xml; charset=UTF-8'

    principal_name = request.app.principal.name
    title = f'{principal_name} {request.translate(_("Gazette"))}'

    rss = Element('rss', attrib={
        'version': '2.0',
        'xmlns:atom': 'http://www.w3.org/2005/Atom'
    })
    channel = sub(rss, 'channel')
    sub(channel, 'title', title)
    sub(channel, 'description', title)
    sub(channel, 'link', request.link(self, name='rss'))
    sub(channel, 'atom:link', None, {
        'href': request.link(self, name='rss'),
        'rel': 'self',
        'type': 'application/rss+xml'
    })
    sub(channel, 'language', request.html_lang)
    sub(channel, 'copyright', principal_name)
    for notice in self.query():
        item = sub(channel, 'item')
        sub(item, 'title', notice.title)
        sub(item, 'description', request.translate(_("Official Notice")))
        sub(item, 'link', request.link(notice, name='view'))
        sub(item, 'guid', request.link(notice, name='view'))
        sub(item, 'pubDate', format_datetime(notice.first_issue))
        sub(item, 'category', notice.organization_object.title)
        sub(item, 'category', notice.category_object.title)

    out = BytesIO()
    ElementTree(rss).write(out, encoding='utf-8', xml_declaration=True)
    out.seek(0)
    return out.read()


@GazetteApp.view(
    model=PublishedNoticeCollection,
    name='pdf',
    permission=Public
)
def view_published_notices_pdf(self, request):
    """ Download the search results as PDF. """

    pdf = Pdf.from_notices(self, request)

    filename = normalize_for_url(
        '{}-{}-{}-{}'.format(
            request.translate(_("Gazette")),
            request.app.principal.name,
            request.translate(_("Search Results")),
            datetime.now().isoformat()
        )
    )

    return Response(
        pdf.read(),
        content_type='application/pdf',
        content_disposition=f'inline; filename={filename}.pdf'
    )


@GazetteApp.form(
    model=PublishedNoticeCollection,
    name='subscribe',
    template='form.pt',
    permission=Public,
    form=SubscriptionForm
)
def view_published_notices_subscribe(self, request, form):
    """ Subscribe by mail to the current query. """

    layout = Layout(self, request)

    if form.submitted(request):

        collection = SubscriptionCollection(request.session)
        subscription = collection.add(
            email=form.email.data,
            locale=request.locale,
            validated=False,
            last_sent=utcnow(),
            term=self.term,
            order=self.order,
            direction=self.direction,
            categories=self.categories,
            organizations=self.organizations,
        )
        send_confirmation_mail(request, subscription)
        request.message(
            _(
                "Thank You! Please check your email to activate your "
                "subscription."
            ),
            'success'
        )

        return redirect(request.link(self))

    callout = ''
    if self.term:
        callout += '{}: {}. '.format(
            request.translate(_("Term")),
            self.term
        )
    if self.categories:
        categories = CategoryCollection(request.session).as_options()
        callout += '{}: {}. '.format(
            request.translate(_("Categories")),
            ', '.join([
                title for value, title in categories
                if value in self.categories
            ])
        )
    if self.organizations:
        organizations = OrganizationCollection(request.session).as_options()
        callout += '{}: {}. '.format(
            request.translate(_("Organizations")),
            ', '.join([
                title for value, title in organizations
                if value in self.organizations
            ])
        )

    return {
        'layout': layout,
        'form': form,
        'title': _("Subscribe"),
        'callout': callout.strip(),
        'button_text': _("Subscribe"),
        'cancel': request.link(self),
    }


@GazetteApp.form(
    model=SubscriptionCollection,
    name='confirm-subscription',
    template='form.pt',
    permission=Public,
    form=SubscriptionConfirmationForm
)
def view_confirm_subscription(self, request, form):
    """ Confirm a subscription. """

    layout = Layout(self, request)

    if form.submitted(request):
        data = request.load_url_safe_token(form.token.data, max_age=86400)
        subscription = self.by_email(data.get('email'))
        if subscription:
            subscription.validated = True
            request.message(
                _("Your subscription has been successfully confirmed."),
                'success'
            )
        return redirect(
            request.link(PublishedNoticeCollection(request.session))
        )

    if 'token' in request.params:
        form.token.data = request.params['token']

    return {
        'layout': layout,
        'form': form,
        'title': _("Confirm subscription"),
        'button_text': _("Confirm"),
        'cancel': request.link(self),
    }
