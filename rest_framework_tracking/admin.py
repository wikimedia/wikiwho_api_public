from django.contrib import admin

from .models import APIRequestLog


class APIRequestLogAdmin(admin.ModelAdmin):
    date_hierarchy = 'requested_at'
    list_display = ('id', 'requested_at', 'response_ms',
                    'view_method', 'page_id',
                    'status_code', 'query_params', 'remote_addr', )
    list_filter = ('view_method', 'status_code', )
    search_fields = ('page_id', 'remote_addr', )


admin.site.register(APIRequestLog, APIRequestLogAdmin)
