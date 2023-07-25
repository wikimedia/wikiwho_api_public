from __future__ import absolute_import, unicode_literals
import logging

from wikiwho_api.celery import app
from deployment.celery_config import worker_name_default, worker_name_user
from django.conf import settings

from base.utils_log import get_base_logger, get_stream_base_logger
from .events_stream import iter_changed_pages, iter_deletion_events
from .tasks import process_article, process_article_deletion, process_article_deletion_from_log_id

# worker_name = app.control.inspect().ping().popitem()[0]
# give name of the worker to speed up
inspector = app.control.inspect([worker_name_default, worker_name_user])
# active: List of tasks currently being executed.
# active_queues: List the task queues a worker are currently consuming from.
# registered: List of registered tasks.
# reserved: List of currently reserved tasks, not including scheduled/active.
# scheduled: List of currently scheduled ETA/countdown tasks.

logger = get_base_logger('events_streamer', settings.EVENTS_STREAM_LOG, level=logging.WARNING)
streamer = get_stream_base_logger('streamer', level=logging.DEBUG)


def get_active_task_pages():
    """Return page titles of tasks that are running right now."""
    try:
        # {'worker_name': [active tasks], 'worker_name2': [..], ..}
        active_tasks = inspector.active() or []
    except ConnectionResetError as e:
        logger.error(
            "The connection has been reset when listing active pages:\n" + str(e) +
            "\nThe reserved_tasks will be assume to be empty")
        reserved_tasks = []
    except Exception as e:
        logger.error("Failed to retrieve active pages:\n" + str(e) +
                     "\nThe reserved_tasks will be assume to be empty")
        reserved_tasks = []
    return [task['args'][2:-3] for worker_name in active_tasks for task in active_tasks[worker_name] or []]


def get_inactive_task_pages():
    """Return page titles of tasks that are registered to Celery. This does not contain tasks in queue."""
    # inspector.scheduled()[worker_name] - we have no scheduled tasks
    try:
        # {'worker_name': [reserved tasks]}
        reserved_tasks = inspector.reserved() or []
    except ConnectionResetError as e:
        logger.error(
            "The connection has been reset when listing inactive pages:\n" + str(e) +
            "\nThe reserved_tasks will be assume to be empty")
        reserved_tasks = []
    except Exception as e:
        logger.error("Failed to retrieve inactive pages:\n" + str(e) +
                     "\nThe reserved_tasks will be assume to be empty")
        reserved_tasks = []

    return [task['args'][2:-3] for worker_name in reserved_tasks for task in reserved_tasks[worker_name] or []]


def process_changed_articles():
    for language, page_title, change in iter_changed_pages(logger):
        # print(len(get_inactive_task_pages()))

        # Delete pickle file if the page is deleted.
        if change.get('type') == 'log' and change.get('log_type') == 'delete' and change.get('log_action') == 'delete':
            streamer.info(f"EVENT (delete): {page_title} ({language})")
            process_article_deletion_from_log_id.delay(language, page_title, change.get('log_id'))
        # Otherwise, queue the article for processing
        elif page_title not in get_inactive_task_pages():
            streamer.info(f"EVENT ({change.get('type')}): {page_title} ({language})")
            # if already not registered to celery
            process_article.delay(language, page_title)


def process_deletion_events():
    for language, page_id in iter_deletion_events(logger):
        streamer.info(f"DELETION EVENT: {page_id} ({language})")
        process_article_deletion(language, page_id)
