from .models import APIRequestLog
from django.utils.timezone import now


class LoggingMixin(object):
    """Mixin to log requests"""
    def initial(self, request, *args, **kwargs):
        """Set current time on request"""
        # get data dict
        try:
            data_dict = request.data.dict()
        except AttributeError:  # if already a dict, can't dictify
            data_dict = request.data

        # get IP
        ipaddr = request.META.get("HTTP_X_FORWARDED_FOR", None)
        if ipaddr:
            # X_FORWARDED_FOR returns client1, proxy1, proxy2,...
            ipaddr = ipaddr.split(", ")[0]
        else:
            ipaddr = request.META.get("REMOTE_ADDR", "")

        # save to log
        self.request.log = APIRequestLog.objects.create(
            requested_at=now(),
            path=request.path,
            remote_addr=ipaddr,
            host=request.get_host(),
            method=request.method,
            query_params=request.query_params.dict(),
            data=data_dict,
        )

        # regular intitial, including auth check
        super(LoggingMixin, self).initial(request, *args, **kwargs)

        # add user to log after auth
        user = request.user
        if user.is_anonymous():
            user = None
        self.request.log.user = user
        self.request.log.save()

    def finalize_response(self, request, response, *args, **kwargs):
        # regular finalize response
        response = super(LoggingMixin, self).finalize_response(request, response, *args, **kwargs)

        # compute response time
        response_timedelta = now() - self.request.log.requested_at
        response_ms = int(response_timedelta.total_seconds() * 1000)

        # save to log
        self.request.log.response = response.rendered_content
        self.request.log.status_code = response.status_code
        self.request.log.response_ms = response_ms
        self.request.log.save()

        # return
        return response
