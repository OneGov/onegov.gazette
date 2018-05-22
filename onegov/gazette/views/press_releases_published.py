from email.utils import format_datetime
from io import BytesIO
from onegov.core.security import Public
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import PublishedPressReleaseCollection
from onegov.gazette.layout import Layout
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import SubElement


@GazetteApp.html(
    model=PublishedPressReleaseCollection,
    template='press_releases_public.pt',
    permission=Public
)
def view_published_press_releases(self, request):
    """ View published press releases. """

    layout = Layout(self, request)

    return {
        'layout': layout,
        'press_releases': self.batch,
    }


@GazetteApp.view(
    model=PublishedPressReleaseCollection,
    name='rss',
    permission=Public
)
def view_published_press_releases_rss(self, request):
    """ Show the published press releases as RSS feed. """

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

    out = BytesIO()
    ElementTree(rss).write(out, encoding='utf-8', xml_declaration=True)
    out.seek(0)
    return out.read()
