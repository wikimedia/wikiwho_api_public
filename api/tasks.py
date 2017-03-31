from __future__ import absolute_import, unicode_literals

# from django.core.cache import cache
from celery import shared_task
# from celery.exceptions import SoftTimeLimitExceeded
from celery_config import default_task_soft_time_limit

from .handler import WPHandler, WPHandlerException


def process_article_task(page_title):
        # if cache.get('page_{}'.format(page_id)) == '1':
        #     return False
        try:
            # with WPHandler(None, page_id=page_id) as wp:
            with WPHandler(page_title) as wp:
                wp.handle(revision_ids=[], is_api_call=False, cache_key_timeout=default_task_soft_time_limit)
        except WPHandlerException as e:
            # if e.code == '03':
                # TODO if underprocess, start a new task??! i dont think is is necessary for now.
            raise e
        return True


@shared_task(soft_time_limit=default_task_soft_time_limit)
def process_article(page_title):
    return process_article_task(page_title)
