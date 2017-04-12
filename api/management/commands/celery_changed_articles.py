from django.core.management.base import BaseCommand

from api.utils_celery import process_changed_articles


class Command(BaseCommand):
    help = "Get event streams of changed articles from wikimedia and create a task for each event."

    # def add_arguments(self, parser):
    #     parser.add_argument('-o', '--output', help='Output folder path for log', required=True)

    def handle(self, *args, **options):
        process_changed_articles()
