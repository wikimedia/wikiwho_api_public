from __future__ import absolute_import, unicode_literals

# from django.core.cache import cache
from celery import shared_task
# from celery.exceptions import SoftTimeLimitExceeded

from deployment.celery_config import default_task_soft_time_limit, long_task_soft_time_limit, user_task_soft_time_limit
from .handler import WPHandler, WPHandlerException


def process_article_task(page_title, timeout, raise_soft_error=False):
        # if cache.get('page_{}'.format(page_id)) == '1':
        #     return False
        try:
            # with WPHandler(None, page_id=page_id) as wp:
            with WPHandler(page_title) as wp:
                # cache_key = wp.cache_key
                wp.handle(revision_ids=[], is_api_call=False, timeout=timeout)
        except WPHandlerException as e:
            if e.code == '03':
                # if article is already under process, simply skip it. TODO wait and start a new task?
                return False
            raise e
        # except SoftTimeLimitExceeded as e:
        #     cache.delete(cache_key)
        #     if raise_soft_error:
        #         # TODO write into csv? but sentry logs them anyway.
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
        result = process_article_task(page_title, default_task_soft_time_limit)
    except WPHandlerException as e1:
        if e1.code in ['00', '10', '11']:
            # if article doesnt exist or wp errors
            raise self.retry(exc=e1)
        else:
            raise e1
    except (ValueError, ConnectionError) as e2:
        raise self.retry(exc=e2)


@shared_task(soft_time_limit=long_task_soft_time_limit)
def process_article_long(page_title):
    process_article_task(page_title, long_task_soft_time_limit, raise_soft_error=True)


@shared_task(soft_time_limit=user_task_soft_time_limit)
def process_article_user(page_title):
    process_article_task(page_title, user_task_soft_time_limit, raise_soft_error=True)
