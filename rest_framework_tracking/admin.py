from django.contrib import admin

from .models import APIRequestLog


class APIRequestLogAdmin(admin.ModelAdmin):
    date_hierarchy = 'requested_at'
    list_display = ('id', 'language', 'requested_at', 'response_ms',
                    'view_method', 'page_id',
                    'status_code', 'query_params', )
    list_filter = ('view_method', 'status_code', 'language', )
    search_fields = ('page_id', )


admin.site.register(APIRequestLog, APIRequestLogAdmin)
