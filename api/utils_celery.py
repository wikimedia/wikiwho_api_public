from __future__ import absolute_import, unicode_literals


from wikiwho_api.celery import app

from .events_stream import iter_changed_page_ids
from .tasks import process_article

worker_name = app.control.inspect().ping().popitem()[0]
# give name of the worker to speed up
inspector = app.control.inspect([worker_name])
# active: List of tasks currently being executed.
# active_queues: List the task queues a worker are currently consuming from.
# registered: List of registered tasks.
# reserved: List of currently reserved tasks, not including scheduled/active.
# scheduled: List of currently scheduled ETA/countdown tasks.


def get_active_task_page_ids():
    """Return page ids of tasks that are running right now."""
    page_ids = []
    """
    [{'worker1.example.com':
    [{'name': 'tasks.sleeptask',
      'id': '32666e9b-809c-41fa-8e93-5ae0c80afbbf',
      'args': '(8,)',
      'kwargs': '{}'}]}]
    """
    for task in inspector.active()[worker_name]:
        page_ids.append(int(task['args'].split(',')[0][1:]))
    return page_ids


def get_inactive_task_page_ids():
    """Return page ids of tasks that are registered to Celery. This does not contain tasks in queue"""
    page_ids = []
    # inspector.scheduled()[worker_name] - we have no scheduled tasks
    tasks = inspector.reserved()[worker_name]
    for task in tasks:
        page_ids.append(int(task['args'].split(',')[0][1:]))
    return page_ids


def process_changed_articles():
    for page_id in iter_changed_page_ids():
        if page_id not in get_inactive_task_page_ids():
            # if already not registered to celery
            process_article.delay(page_id)
