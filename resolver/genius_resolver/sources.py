"""Bounded public GitHub discovery; source content is inert, never executable."""
import json
import urllib.parse
import urllib.request

QUERIES = (
    'is:issue is:open is:public no:assignee label:"help wanted" label:documentation',
    'is:issue is:open is:public no:assignee label:"help wanted" label:bug language:Python',
)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('SOURCE_REDIRECT_REJECTED')


def search(query, opener=None):
    if query not in QUERIES:
        raise ValueError('REVIEW_QUERY_IN_CODE_FIRST')
    url = 'https://api.github.com/search/issues?' + urllib.parse.urlencode(
        dict(q=query, sort='updated', order='desc', per_page=10))
    request = urllib.request.Request(url, headers={
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'Genius-Problem-Resolver/1 (github.com/pedrosalvadeo/genius-decision-open)',
    })
    opener = opener or urllib.request.build_opener(NoRedirect())
    with opener.open(request, timeout=15) as response:
        if response.status != 200:
            raise ValueError('SOURCE_HTTP_STATUS')
        raw = response.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError('SOURCE_RESPONSE_LIMIT')
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get('items'), list) or len(data['items']) > 10:
        raise ValueError('SOURCE_SEARCH_SCHEMA')
    return data
