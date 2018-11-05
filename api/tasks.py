from __future__ import absolute_import, unicode_literals
from simplejson import JSONDecodeError
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from requests import ReadTimeout

from django.core.cache import cache

from deployment.celery_config import default_task_soft_time_limit, user_task_soft_time_limit, long_task_soft_time_limit
from .handler import WPHandler, WPHandlerException
from .models import LongFailedArticle
# from wikiwho.utils_db import wikiwho_to_db


def process_article_task(language, page_title, page_id=None, revision_id=None,
                         cache_key_timeout=0, raise_soft_time_limit=False):
    # if cache.get('page_{}'.format(page_id)) == '1':
    #     return False
    cache_key = None
    try:
        with WPHandler(page_title, page_id=page_id, revision_id=revision_id, language=language) as wp:
            cache_key = wp.cache_key
            wp.handle(revision_ids=[], is_api_call=False, timeout=cache_key_timeout)
    except WPHandlerException as e:
        if cache_key:
            cache.delete(cache_key)
        if e.code in ['03', '00']:
            # 03: if article is already under process, simply skip it. TODO wait and start a new task?
            # 00: ignore 'article doesnt exist' errors
            return False
        raise e
    except SoftTimeLimitExceeded as e:
        cache.delete(cache_key)
        if raise_soft_time_limit:
            failed_rev_id = int(wp.wikiwho.revision_curr.id)
            failed_article, created = LongFailedArticle.objects.get_or_create(page_id=wp.page_id,
                                                                              language=language,
                                                                              defaults={'count': 1,
                                                                                        'title': wp.saved_article_title or '',
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
            process_article_long.delay(language, wp.saved_article_title or '', wp.page_id, revision_id)
    #         process_article_long.apply_async([page_title], queue='long_lasting')
    return True


# retry max 6 times (default value of max_retries is 3) and
# wait 360 seconds (default value of default_retry_delay is 180) between each retry.
@shared_task(bind=True, soft_time_limit=default_task_soft_time_limit, max_retries=6, default_retry_delay=6 * 60)
def process_article(self, language, page_title):
    try:
        process_article_task(language, page_title, cache_key_timeout=default_task_soft_time_limit)
    except WPHandlerException as e:
        if e.code =='40':
            # 40: Non-pickled articles are ignored during staging
            self.update_state(state="IGNORED")
            return e.message
        elif e.code in ['10', '11']:
            # if wp errors
            # NOTE: actually 10 should not occur because we set is_api_call=False in the process_article_task!
            raise self.retry(exc=e)
        else:
            raise e
    except (ValueError, ConnectionError, ReadTimeout, JSONDecodeError) as e:
        # ReadTimeout -> requests timeout
        # JSONDecodeError -> WP api error from get_latest_revision_data or create_wp_session
        # FIXME are ConnectionResetError and ProtocolError during requests.get occurs due to SoftTimeLimitExceeded?
        raise self.retry(exc=e)


# retry max 6 times (default value of max_retries is 3) and
# wait 360 seconds (default value of default_retry_delay is 180) between each retry.
@shared_task(bind=True, soft_time_limit=user_task_soft_time_limit, max_retries=6, default_retry_delay=6 * 60)
def process_article_user(self, language, page_title, page_id=None, revision_id=None):
    try:
        process_article_task(language, page_title, page_id, revision_id, cache_key_timeout=user_task_soft_time_limit)
    except WPHandlerException as e:
        if e.code =='40':
            # 40: Non-pickled articles are ignored during staging
            self.update_state(state="IGNORED")
            return e.message
        elif e.code in ['10', '11']:
            # if wp errors
            # NOTE: actually 10 should not occur because we set is_api_call=False in the process_article_task!
            raise self.retry(exc=e)
        else:
            raise e
    except (ValueError, ConnectionError, ReadTimeout, JSONDecodeError) as e:
        raise self.retry(exc=e)


# retry max 6 times (default value of max_retries is 3) and
# wait 360 seconds (default value of default_retry_delay is 180) between each retry.
@shared_task(bind=True, soft_time_limit=long_task_soft_time_limit, max_retries=6, default_retry_delay=6 * 60)
def process_article_long(self, language, page_title, page_id=None, revision_id=None):
    try:
        process_article_task(language, page_title, page_id, revision_id,
                             cache_key_timeout=long_task_soft_time_limit,
                             raise_soft_time_limit=True)
    except WPHandlerException as e:
        if e.code =='40':
            # 40: Non-pickled articles are ignored during staging
            self.update_state(state="IGNORED")
            return e.message
        elif e.code in ['10', '11']:
            # if wp errors
            # NOTE: actually 10 should not occur because we set is_api_call=False in the process_article_task!
            raise self.retry(exc=e)
        else:
            raise e
    except (ValueError, ConnectionError, ReadTimeout, JSONDecodeError) as e:
        raise self.retry(exc=e)


# # retry max 3 times (default value of max_retries) and
# # wait 180 seconds (default value of default_retry_delay) between each retry.
# @shared_task(bind=True, soft_time_limit=db_time_limit)
# def wikiwho_to_db_task(self, wikiwho, language, save_tables=('article', 'revision', 'token',)):
#     try:
#         wikiwho_to_db(wikiwho, language, save_tables)
#     except Exception as e:
#         raise self.retry(exc=e)
