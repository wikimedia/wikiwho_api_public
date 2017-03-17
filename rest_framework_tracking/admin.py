from django.contrib import admin

from .models import APIRequestLog


class APIRequestLogAdmin(admin.ModelAdmin):
    date_hierarchy = 'requested_at'
    list_display = ('id', 'requested_at', 'response_ms',
                    'view_method', 'page_id',
                    'user', 'remote_addr', 'host',
                    'status_code', 'query_params', )
    list_filter = ('view_method', 'status_code', )
    search_fields = ('user__email', 'page_id', )
    raw_id_fields = ('user', )


admin.site.register(APIRequestLog, APIRequestLogAdmin)
