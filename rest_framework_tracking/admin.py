from django.contrib import admin
from .models import APIRequestLog


class APIRequestLogAdmin(admin.ModelAdmin):
    date_hierarchy = 'requested_at'
    list_display = ('id', 'requested_at', 'response_ms',
                    'user', 'path', 'query_params', 'remote_addr', 'host')
    list_filter = ('user', 'path', 'query_params', 'remote_addr', 'host')

admin.site.register(APIRequestLog, APIRequestLogAdmin)
