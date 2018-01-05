from json import loads

import urllib3
from urllib3.exceptions import ProtocolError
from sseclient import SSEClient


class EventSource(SSEClient):

    def _read(self):
        """Read the incoming event source stream and yield event chunks.

        Unfortunately it is possible for some servers to decide to break an
        event into multiple HTTP chunks in the response. It is thus necessary
        to correctly stitch together consecutive response chunks and find the
        SSE delimiter (empty new line) to yield full, correct event chunks."""
        data = ''
        for chunk in self._event_source:
            for line in chunk.splitlines(True):
                if not line.strip():
                    yield data
                    data = ''
                # ignore decoding errors, we only need page id and namespace which are numbers and doesn't contain
                # special chars
                data += line.decode(self._char_enc, errors='ignore')
        if data:
            yield data


def stream_response(url):
    """Get a streaming response for the given event feed using urllib3."""
    http = urllib3.PoolManager()
    # the .stream(chunk_size) is important here!  Without it, the
    # response body seems to be accessed in an inefficient manner.
    return http.request('GET', url, preload_content=False).stream(1024)


def stream_response_with_requests(url):
    """Get a streaming response for the given event feed using requests."""
    import requests
    # TODO The id field can be used to tell EventStreams to start consuming from an earlier
    # position in the stream. This enables clients to automatically resume from where they
    # left off if they are disconnected.
    # https://wikitech.wikimedia.org/wiki/EventStreams
    # headers = {'Last-Event-ID': [{"topic": "codfw.mediawiki.recentchange", "partition": 0, "offset": -1},
    #                              {"topic": "eqiad.mediawiki.recentchange", "partition": 0, "offset": 431056994}]}
    # return requests.get(url, stream=True, headers=headers)
    return requests.get(url, stream=True)


def iter_changed_pages():
    while True:
        try:
            url = 'https://stream.wikimedia.org/v2/stream/recentchange'
            event_source = stream_response(url)
            # event_source = stream_response_with_requests(url)
            # import time
            # start = time.time()
            # counter = 0
            for event in EventSource(event_source).events():
                # page_id = event.data.split('"id":')[1].split(',"')[0] --> this is event id!
                data = event.data
                if not data:
                    continue
                # page_title = data.split('"title":')[1].split(',"')[0][1:-1]
                # if data.split('"wiki":"')[1].split('"')[0] == 'enwiki' and \
                #    data.split('"namespace":')[1].split(',"')[0] == '0' and \
                #    page_title and page_title != 'null' and \
                #    data.split('"type":"')[1].split('"')[0] in ['edit', 'new']:
                #     # counter += 1
                #     yield page_title  # , time.time() - start, counter
                try:
                    change = loads(data)
                except ValueError:  # JSONDecodeError
                    continue
                page_title = change.get('title')
                wiki = change.get('wiki')
                wikis = ['enwiki', 'euwiki', 'dewiki', 'trwiki', 'eswiki']
                if wiki in wikis and change.get('namespace') == 0 and \
                   page_title and change.get('type') in ['edit', 'new']:
                    language = wiki.split('wiki')[0]
                    # yield change
                    yield language, page_title
        except ProtocolError as e:
            # restart events stream
            pass
