from __future__ import absolute_import, unicode_literals
from celery import shared_task
# from celery.exceptions import SoftTimeLimitExceeded
from requests import ReadTimeout

from django.core.cache import cache

from deployment.celery_config import default_task_soft_time_limit, user_task_soft_time_limit
from .handler import WPHandler, WPHandlerException


def process_article_task(page_title, page_id=None, revision_id=None, timeout=0):
    # if cache.get('page_{}'.format(page_id)) == '1':
    #     return False
    cache_key = None
    try:
        with WPHandler(page_title, page_id=page_id, revision_id=revision_id) as wp:
            cache_key = wp.cache_key
            wp.handle(revision_ids=[], is_api_call=False, timeout=timeout)
    except WPHandlerException as e:
        if cache_key:
            cache.delete(cache_key)
        if e.code == '03':
            # if article is already under process, simply skip it. TODO wait and start a new task?
            return False
        raise e
    # except SoftTimeLimitExceeded as e:
    #     cache.delete(cache_key)
    #     if raise_error:
    #         raise e
    #     else:
    #         process_article_long.delay(page_title)
    #         process_article_long.apply_async([page_title], queue='long_lasting')
    return True


# retry max 3 times (default value of max_retries) and
# wait 180 seconds (default value of default_retry_delay) between each retry.
@shared_task(bind=True, soft_time_limit=default_task_soft_time_limit)
def process_article(self, page_title):
    try:
        process_article_task(page_title, timeout=default_task_soft_time_limit)
    except WPHandlerException as e:
        if e.code in ['00', '10', '11']:
            # if article doesnt exist or wp errors
            # NOTE: actually 01 should not occur because we set is_api_call=False in the process_article_task!
            raise self.retry(exc=e)
        else:
            raise e
    except (ValueError, ConnectionError, ReadTimeout) as e:
        # ReadTimeout -> requests timeout
        # FIXME are ConnectionResetError and ProtocolError during requests.get occurs due to SoftTimeLimitExceeded?
        raise self.retry(exc=e)


# @shared_task(soft_time_limit=long_task_soft_time_limit)
# def process_article_long(page_title):
#     process_article_task(page_title, timeout=long_task_soft_time_limit, raise_error=True)


@shared_task(bind=True, soft_time_limit=user_task_soft_time_limit)
def process_article_user(self, page_title, page_id=None, revision_id=None):
    try:
        process_article_task(page_title, page_id, revision_id, timeout=user_task_soft_time_limit)
    except WPHandlerException as e:
        if e.code in ['00', '10', '11']:
            # if article doesnt exist or wp errors
            # NOTE: actually 01 should not occur because we set is_api_call=False in the process_article_task!
            raise self.retry(exc=e)
        else:
            raise e
    except (ValueError, ConnectionError, ReadTimeout) as e:
        raise self.retry(exc=e)
