from __future__ import absolute_import, unicode_literals

from wikiwho_api.celery import app
from deployment.celery_config import worker_name_default, worker_name_user

from .events_stream import iter_changed_pages
from .tasks import process_article
# from .utils_pickles import get_pickle_size

# worker_name = app.control.inspect().ping().popitem()[0]
# give name of the worker to speed up
inspector = app.control.inspect([worker_name_default, worker_name_user])
# active: List of tasks currently being executed.
# active_queues: List the task queues a worker are currently consuming from.
# registered: List of registered tasks.
# reserved: List of currently reserved tasks, not including scheduled/active.
# scheduled: List of currently scheduled ETA/countdown tasks.


def get_active_task_pages():
    """Return page titles of tasks that are running right now."""
    active_tasks = inspector.active() or []  # {'worker_name': [active tasks], 'worker_name2': [..], ..}
    """
    task:
    [{'worker1.example.com':
    [{'name': 'tasks.sleeptask',
      'id': '32666e9b-809c-41fa-8e93-5ae0c80afbbf',
      'args': '(8/"title",)',
      'kwargs': '{}'}]}]
    """
    return [task['args'][2:-3] for worker_name in active_tasks for task in active_tasks[worker_name] or []]


def get_inactive_task_pages():
    """Return page titles of tasks that are registered to Celery. This does not contain tasks in queue."""
    # inspector.scheduled()[worker_name] - we have no scheduled tasks
    reserved_tasks = inspector.reserved() or []  # {'worker_name': [reserved tasks]}
    return [task['args'][2:-3] for worker_name in reserved_tasks for task in reserved_tasks[worker_name] or []]


def process_changed_articles():
    for page_title in iter_changed_pages():
        # print(len(get_inactive_task_pages()))
        if page_title not in get_inactive_task_pages():
            # if already not registered to celery
            process_article.delay(page_title)
            # FIXME event data doesnt contain pageid! decide a limit + settings.PICKLE_BIG_SIZE_LIMIT
            # if get_pickle_size(page_id) > 446197:
            #     process_big_sized_article.delay(page_title)
            # else:
            #     process_article.delay(page_title)
