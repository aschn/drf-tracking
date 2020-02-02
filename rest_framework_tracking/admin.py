from django.conf import settings
from django.contrib import admin
from .models import APIRequestLog


class APIRequestLogAdmin(admin.ModelAdmin):
    date_hierarchy = 'requested_at'
    list_display = ('id', 'requested_at', 'response_ms', 'status_code',
                    'user', 'method',
                    'path', 'remote_addr', 'host',
                    'query_params')
    list_filter = ('method', 'status_code')
    search_fields = ('path', 'user__email',)
    raw_id_fields = ('user', )

    if getattr(settings, 'DRF_TRACKING_ADMIN_LOG_READONLY', False):
        readonly_fields = ('user', 'username_persistent', 'requested_at',
                           'response_ms', 'path', 'view', 'view_method',
                           'remote_addr', 'host', 'method', 'query_params',
                           'data', 'response', 'errors', 'status_code')


admin.site.register(APIRequestLog, APIRequestLogAdmin)
