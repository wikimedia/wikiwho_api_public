from django.core.management.base import BaseCommand

from api.utils_celery import process_deletion_events


class Command(BaseCommand):
    help = "Get event streams of deletion events from wikimedia and create tasks to delete the associated pickle files."

    def handle(self, *args, **options):
        process_deletion_events()
