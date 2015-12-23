from .models import APIRequestLog
from django.utils.timezone import now


class LoggingMixin(object):
    """Mixin to log requests"""
    def initialize_request(self, request, *args, **kwargs):
        """Set current time on request"""
        # regular intitialize
        request = super(LoggingMixin, self).initialize_request(request, *args, **kwargs)

        # get user
        if request.user.is_authenticated():
            user = request.user
        else:  # AnonymousUser
            user = None

        # get data dict
        try:
            data_dict = request.data.dict()
        except AttributeError:  # if already a dict, can't dictify
            data_dict = request.data

        # get IP
        ip = request.META.get("HTTP_X_FORWARDED_FOR", None)
        if ip:
            # X_FORWARDED_FOR returns client1, proxy1, proxy2,...
            ip = ip.split(", ")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "")

        # save to log
        request.log = APIRequestLog.objects.create(
            user=user,
            requested_at=now(),
            path=request.path,
            remote_addr=ip,
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
