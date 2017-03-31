# import json
import urllib3
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
    return requests.get(url, stream=True)


def iter_changed_pages():
    # page_ids = []
    url = 'https://stream.wikimedia.org/v2/stream/recentchange'
    event_source = stream_response(url)
    # event_source = stream_response_with_requests(url)
    for event in EventSource(event_source).events():
        # print(event.data)  # "id":926316704,"
        # page_id = event.data.split('"id":')[1].split(',"')[0] --> this is event id!
        page_title = event.data.split('"title":')[1].split(',"')[0][1:-1]
        namespace = event.data.split('"namespace":')[1].split(',"')[0]
        wiki = event.data.split('"wiki":"')[1].split('"')[0]
        if wiki == 'enwiki' and namespace == '0' and page_title and page_title != 'null':
            yield page_title
            # page_ids.append(page_id)
            # print(len(page_ids), len(set(page_ids)))
        # change = json.loads(event.data)
        # if change['wiki'] == 'enwiki' and change['namespace'] == 0:
        #     page_id = change['id']
        #     if page_id:
        #         yield page_id
