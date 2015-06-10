from django.db import models
from django.conf import settings


class APIRequestLog(models.Model):
    """Logs API requests by time, user, etc"""
    # user or None for anon
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)

    # timestamp of request
    requested_at = models.DateTimeField(db_index=True)

    # number of milliseconds to respond
    response_ms = models.PositiveIntegerField(default=0)

    # request path
    path = models.CharField(max_length=200, db_index=True)

    # remote IP address of request
    remote_addr = models.GenericIPAddressField()

    # originating host of request
    host = models.URLField()

    # HTTP method (GET, etc)
    method = models.CharField(max_length=10)

    # query params
    query_params = models.TextField(db_index=True)

    # POST body data
    data = models.TextField(null=True, blank=True)

    # response
    response = models.TextField(null=True, blank=True)

    # status code
    status_code = models.PositiveIntegerField(null=True, blank=True)
