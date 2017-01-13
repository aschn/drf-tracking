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


admin.site.register(APIRequestLog, APIRequestLogAdmin)
