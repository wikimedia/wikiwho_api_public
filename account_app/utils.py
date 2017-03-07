import datetime

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User


def get_expired_users(activation_days=None):
    if activation_days is None:
        activation_days = settings.ACCOUNT_ACTIVATION_DAYS
    if settings.USE_TZ:
        now = timezone.now()
    else:
        now = datetime.datetime.now()
    return User.objects.exclude(is_active=True).filter(date_joined__lt=now - datetime.timedelta(activation_days))
