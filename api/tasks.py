
from __future__ import absolute_import, unicode_literals

from celery import shared_task

from .handler import WPHandler
from .events_stream import iter_changed_page_ids

@shared_task
def process_article(page_id):
    print(page_id)
    # with WPHandler(None, page_id=page_id) as wp:
    #     wp.handle(revision_ids=[], is_api_call=False)
    return True


def process_changed_articles():
    for page_id in iter_changed_page_ids():
        process_article.delay(page_id)
