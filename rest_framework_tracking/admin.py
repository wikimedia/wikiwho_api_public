from django.contrib import admin

from .models import APIRequestLog


class APIRequestLogAdmin(admin.ModelAdmin):
    date_hierarchy = 'requested_at'
    list_display = ('id', 'language', 'requested_at', 'response_ms',
                    'view_class', 'view_method', 'instance_id', 'type_id',
                    'status_code', 'query_params','remote_addr', )
    list_filter = ('language', 'view_class', 'view_method', 'status_code', 'type_id')
    search_fields = ('instance_id','remote_addr', )


admin.site.register(APIRequestLog, APIRequestLogAdmin)
