from django.db import models
# from django.conf import settings

# from .managers import PrefetchUserManager


class BaseAPIRequestLog(models.Model):
    """Logs API requests by time, user, etc"""
    # user or None for anon
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)

    # timestamp of request
    requested_at = models.DateTimeField(db_index=True)

    # number of milliseconds to respond
    response_ms = models.PositiveIntegerField(default=0)

    # request path
    # path = models.CharField(max_length=200, db_index=True)
    # path = models.CharField(max_length=200)

    # view called by the path
    # view = models.CharField(max_length=200, db_index=True)

    # method of the view
    view_method = models.CharField(max_length=200, db_index=True)

    # remote IP address of request
    # remote_addr = models.GenericIPAddressField()

    # originating host of request
    # host = models.URLField()

    # HTTP method (GET, etc)
    # method = models.CharField(max_length=10)

    # query params
    # query_params = models.TextField(null=True, blank=True)
    query_params = models.CharField(max_length=256, default='', blank=True)

    # POST body data
    # data = models.TextField(null=True, blank=True)

    # response
    # response = models.TextField(null=True, blank=True)

    # error traceback
    # errors = models.TextField(null=True, blank=True)

    # status code
    status_code = models.PositiveIntegerField(null=True, blank=True)

    # custom manager
    # objects = PrefetchUserManager()

    class Meta:
        abstract = True


class APIRequestLog(BaseAPIRequestLog):
    page_id = models.IntegerField(blank=True, null=True, db_index=True, help_text='Article id')
