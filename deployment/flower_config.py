"""
celery -A wikiwho_api flower --conf='deployment/flower_config.py'
default is flowerconfig.py
"""
# from flower.utils.template import humanize


# def format_task(task):
#     task.args = humanize(task.args, length=10)
#     task.kwargs.pop('credit_card_number')
#     task.result = humanize(task.result, length=20)
#     return task

persistent = True  # default False
max_tasks = 10000  # default 10000
# tasks_columns = 'name'
