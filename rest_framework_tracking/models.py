from django.db import models, connection
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
    view_method = models.CharField(max_length=200)
    view_class = models.CharField(max_length=200)

    # remote IP address of request
    # remote_addr = models.GenericIPAddressField(null=True)

    # originating host of request
    # host = models.URLField(null=True)

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

    language = models.CharField(max_length=8, default='',
                                choices=(('', '-------'), ('en', 'English'), ('de', 'German'), ('eu', 'Basque')))

    @classmethod
    def overview(cls):
        with connection.cursor() as cursor:
            q = """
            select date_trunc('month', requested_at) as year_month, language, count(*) 
            from rest_framework_tracking_apirequestlog  
            group by month, language 
            order by month;
            """
            cursor.execute(q)
            rows = cursor.fetchall()
        return rows

    class Meta:
        abstract = True


class APIRequestLog(BaseAPIRequestLog):
    page_id = models.IntegerField(blank=True, null=True, db_index=True, help_text='Article id')
