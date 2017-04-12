"""Celery configuration file."""
import multiprocessing
from django.conf import settings
# from celery.worker.autoscale import Autoscaler as BaseAutoscaler, AUTOSCALE_KEEPALIVE
# from kombu import Exchange, Queue

# CELERY_BROKER_URL = 'amqp://guest:guest@localhost//'
# CELERY_BROKER_URL = 'pyamqp://guest@localhost//'
# http://docs.celeryproject.org/en/latest/getting-started/brokers/rabbitmq.html
# CELERY_BROKER_URL
# broker_url = 'amqp://localhost'  # RabbitMQ
broker_url = 'amqp://guest:guest@localhost:5672//'
#: Only add pickle to this list if your broker is secured
#: from unwanted access (see userguide/security.html)
accept_content = ['json']  # CELERY_ACCEPT_CONTENT
# CELERY_RESULT_BACKEND = 'db+sqlite:///results.sqlite'
task_serializer = 'json'  # CELERY_TASK_SERIALIZER
timezone = settings.TIME_ZONE
enable_utc = False

worker_name = 'worker1@ww_host'  # check /etc/default/celeryd
# task_soft_time_limit = 4  # seconds
default_task_soft_time_limit = 1800  # 30 minutes
long_task_soft_time_limit = 3600  # 1 hour
user_task_soft_time_limit = long_task_soft_time_limit

# task_queues = (
#     Queue('default', queue_arguments={'x-max-priority': 1, }, ),
#     Queue('long', Exchange('long'), routing_key='long', queue_arguments={'x-max-priority': 3}, ),
#     Queue('user', Exchange('user'), routing_key='user', queue_arguments={'x-max-priority': 2}, ),
# )
# task_routes = {
#         'api.tasks.process_article': {
#             'queue': 'default',
#         },
#         'api.tasks.process_article_long': {
#             'queue': 'long',
#             'routing_key': 'long',
#         },
#         'api.tasks.process_article_user': {
#             'queue': 'user',
#             'routing_key': 'user',
#         },
# }
if settings.DEBUG:
    worker_concurrency = int(multiprocessing.cpu_count() / 3) + 1
else:
    worker_concurrency = 12
# class Autoscaler(BaseAutoscaler):
#     def __init__(self, pool, max_concurrency,
#                  min_concurrency=0, worker=None,
#                  keepalive=AUTOSCALE_KEEPALIVE, mutex=None):
#         super(Autoscaler, self).__init__(pool=pool,
#                                          max_concurrency=int(multiprocessing.cpu_count() / 2),
#                                          min_concurrency=int(multiprocessing.cpu_count() / 3),
#                                          worker=worker, keepalive=keepalive, mutex=mutex)
# worker_autoscaler = Autoscaler
