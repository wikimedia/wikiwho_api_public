from json import loads

import urllib3
from urllib3.exceptions import ProtocolError
from sseclient import SSEClient
import certifi
from django.conf import settings


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
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
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


def iter_changed_pages(logger):
    wikis = settings.EVENT_STREAM_WIKIS
    while True:
        try:
            url = 'https://stream.wikimedia.org/v2/stream/recentchange'
            event_source = stream_response(url)

            for event in EventSource(event_source).events():
                data = event.data
                if not data:
                    continue
                try:
                    change = loads(data)
                except ValueError:  # JSONDecodeError
                    continue
                page_title = change.get('title')
                wiki = change.get('wiki')
                if wiki in wikis and change.get('namespace') == 0 and page_title:
                    language = change.get('server_name').split('.')[0]
                    # yield language, page_title, action
                    # Do this only for applicable event types.
                    if change.get('type') in ['edit', 'new']:
                        yield language, page_title, change
                    elif change.get('type') == 'log' and change.get('log_type') == 'delete' and \
                            change.get('log_action') == 'delete':
                        yield language, page_title, change
        except ProtocolError as e:
            # restart events stream
            pass
        except Exception as e:
            logger.error("Unexpected error retrieving event:\n" + str(e) + ".\nThe process will continue anyway.")


# Listens to the mediawiki.revision-visibility-change stream which announces revision deletion and suppression events.
# Full page deletion is still handled by the main EventStreams listener.
def iter_deletion_events(logger):
    wikis = settings.EVENT_STREAM_WIKIS
    while True:
        try:
            url = 'https://stream.wikimedia.org/v2/stream/mediawiki.revision-visibility-change'
            event_source = stream_response(url)

            for event in EventSource(event_source).events():
                data = event.data
                if not data:
                    continue
                try:
                    change = loads(data)
                except ValueError:
                    continue

                page_id = change.get('page_id')
                if change.get('database') in wikis and change.get('page_namespace') == 0 and page_id:
                    before = change.get('prior_state').get('visibility')
                    after = change.get('visibility')

                    # Only act if there was a change in visibility.
                    if (before.get('text') and not after.get('text')) or \
                            (before.get('user') and not after.get('user')) or \
                            (not before.get('text') and after.get('text')) or \
                            (not before.get('user') and after.get('user')):
                        language = change.get('meta').get('domain').split('.')[0]
                        # yield language, page_Id
                        yield language, page_id
        except ProtocolError as e:
            # restart events stream
            pass
        except Exception as e:
            logger.error("Unexpected error retrieving event:\n" + str(e) + ".\nThe process will continue anyway.")
