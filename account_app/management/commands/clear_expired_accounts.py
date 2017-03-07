from django.core.management.base import BaseCommand

from account_app.utils import get_expired_users


class Command(BaseCommand):
    help = "Deletes expired accounts and users."

    def add_arguments(self, parser):
        parser.add_argument('-d', '--activation_days', type=int, default=None, required=False,
                            help='Delete accounts not active after activation_days from joined date')

    def handle(self, *args, **options):
        activation_days = options['activation_days']
        print(get_expired_users(activation_days).delete())
