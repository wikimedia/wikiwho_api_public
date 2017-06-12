from __future__ import absolute_import, unicode_literals
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from requests import ReadTimeout

from django.core.cache import cache

from deployment.celery_config import default_task_soft_time_limit, user_task_soft_time_limit, long_task_soft_time_limit
from .handler import WPHandler, WPHandlerException
from .models import LongFailedArticle


def process_article_task(page_title, page_id=None, revision_id=None, cache_key_timeout=0, raise_soft_time_limit=False):
    # if cache.get('page_{}'.format(page_id)) == '1':
    #     return False
    cache_key = None
    try:
        with WPHandler(page_title, page_id=page_id, revision_id=revision_id) as wp:
            cache_key = wp.cache_key
            wp.handle(revision_ids=[], is_api_call=False, timeout=cache_key_timeout)
    except WPHandlerException as e:
        if cache_key:
            cache.delete(cache_key)
        if e.code == '03':
            # if article is already under process, simply skip it. TODO wait and start a new task?
            return False
        raise e
    except SoftTimeLimitExceeded as e:
        cache.delete(cache_key)
        if raise_soft_time_limit:
            failed_rev_id = int(wp.wikiwho.revision_curr.id)
            failed_article, created = LongFailedArticle.objects.get_or_create(id=wp.page_id,
                                                                              defaults={'count': 1,
                                                                                        'title': page_title,
                                                                                        'revisions': [failed_rev_id]})
            if not created:
                failed_article.count += 1
                if failed_rev_id not in failed_article.revisions:
                    failed_article.revisions.append(failed_rev_id)
                    failed_article.save(update_fields=['count', 'modified', 'revisions'])
                else:
                    failed_article.save(update_fields=['count', 'modified'])
            raise e
        else:
            process_article_long.delay(page_title, page_id, revision_id)
    #         process_article_long.apply_async([page_title], queue='long_lasting')
    return True


# retry max 3 times (default value of max_retries) and
# wait 180 seconds (default value of default_retry_delay) between each retry.
@shared_task(bind=True, soft_time_limit=default_task_soft_time_limit)
def process_article(self, page_title):
    try:
        process_article_task(page_title, cache_key_timeout=default_task_soft_time_limit)
    except WPHandlerException as e:
        if e.code in ['00', '10', '11']:
            # if article doesnt exist or wp errors
            # NOTE: actually 10 should not occur because we set is_api_call=False in the process_article_task!
            raise self.retry(exc=e)
        elif e.code == '00':
            # ignore 'article doesnt exist' errors
            return False
        else:
            raise e
    except (ValueError, ConnectionError, ReadTimeout) as e:
        # ReadTimeout -> requests timeout
        # FIXME are ConnectionResetError and ProtocolError during requests.get occurs due to SoftTimeLimitExceeded?
        raise self.retry(exc=e)


@shared_task(bind=True, soft_time_limit=user_task_soft_time_limit)
def process_article_user(self, page_title, page_id=None, revision_id=None):
    try:
        process_article_task(page_title, page_id, revision_id, cache_key_timeout=user_task_soft_time_limit)
    except WPHandlerException as e:
        if e.code in ['00', '10', '11']:
            # if article doesnt exist or wp errors
            # NOTE: actually 10 should not occur because we set is_api_call=False in the process_article_task!
            raise self.retry(exc=e)
        else:
            raise e
    except (ValueError, ConnectionError, ReadTimeout) as e:
        raise self.retry(exc=e)


# retry max 3 times (default value of max_retries) and
# wait 180 seconds (default value of default_retry_delay) between each retry.
@shared_task(bind=True, soft_time_limit=long_task_soft_time_limit)
def process_article_long(self, page_title, page_id=None, revision_id=None):
    try:
        process_article_task(page_title, page_id, revision_id,
                             cache_key_timeout=long_task_soft_time_limit,
                             raise_soft_time_limit=True)
    except WPHandlerException as e:
        if e.code in ['00', '10', '11']:
            # if article doesnt exist or wp errors
            # NOTE: actually 10 should not occur because we set is_api_call=False in the process_article_task!
            raise self.retry(exc=e)
        else:
            raise e
    except (ValueError, ConnectionError, ReadTimeout) as e:
        raise self.retry(exc=e)
