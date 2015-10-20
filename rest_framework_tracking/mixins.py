from .models import APIRequestLog
from django.utils.timezone import now

from rest_framework import exceptions
from ipware.ip import get_real_ip


class LoggingMixin(object):
    """Mixin to log requests"""
    def initialize_request(self, request, *args, **kwargs):
        """Set current time on request"""
        # regular intitialize
        request = super(LoggingMixin, self).initialize_request(request, *args, **kwargs)

        # get user
        try:
            if request.user.is_authenticated():
                user = request.user
            else:  # AnonymousUser
                user = None
        except exceptions.AuthenticationFailed:
            # The AuthenticationFailed exception could be raised by any
            # authentication backend based in tokens, when those expired.
            user = None

        # get data dict
        try:
            data_dict = request.data.dict()
        except AttributeError:  # if already a dict, can't dictify
            data_dict = request.data

        # save to log
        request.log = APIRequestLog.objects.create(
            user=user,
            requested_at=now(),
            path=request.path,
            remote_addr=get_real_ip(request),
            host=request.get_host(),
            method=request.method,
            query_params=request.query_params.dict(),
            data=data_dict,
        )

        # return
        return request

    def finalize_response(self, request, response, *args, **kwargs):
        # regular finalize response
        response = super(LoggingMixin, self).finalize_response(request, response, *args, **kwargs)

        # compute response time
        response_timedelta = now() - request.log.requested_at
        response_ms = int(response_timedelta.total_seconds() * 1000)

        # save to log
        request.log.response = response.rendered_content
        request.log.status_code = response.status_code
        request.log.response_ms = response_ms
        request.log.save()

        # return
        return response
