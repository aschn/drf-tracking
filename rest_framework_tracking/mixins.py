from .models import APIRequestLog
from django.utils.timezone import now


class LoggingMixin(object):
    """Mixin to log requests"""
    def initialize_request(self, request, *args, **kwargs):
        """Set current time on request"""
        # regular intitialize
        request = super(LoggingMixin, self).initialize_request(request, *args, **kwargs)

        # set time
        request.timestamp = now()

        # return
        return request

    def finalize_response(self, request, response, *args, **kwargs):
        # get user
        if request.user.is_authenticated():
            user = request.user
        else:  # AnonymousUser
            user = None

        # compute response time
        response_timedelta = now() - request.timestamp
        response_ms = int(response_timedelta.total_seconds() * 1000)

        # get data dict
        try:
            data_dict = request.data.dict()
        except AttributeError:  # if already a dict, can't dictify
            data_dict = request.data

        # regular finalize response
        response = super(LoggingMixin, self).finalize_response(request, response, *args, **kwargs)

        # save to log
        APIRequestLog.objects.create(
            user=user,
            requested_at=request.timestamp,
            response_ms=response_ms,
            path=request.path,
            remote_addr=request.META['REMOTE_ADDR'],
            host=request.get_host(),
            method=request.method,
            query_params=request.query_params.dict(),
            data=data_dict,
            response=response.rendered_content,
            status_code=response.status_code,
        )

        # return
        return response
