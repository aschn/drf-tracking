from .models import APIRequestLog
from rest_framework.exceptions import UnsupportedMediaType
from django.utils.timezone import now
import traceback


class LoggingMixin(object):
    logging_methods = '__all__'

    """Mixin to log requests"""
    def initial(self, request, *args, **kwargs):
        """Set current time on request"""

        # check if request method is being logged
        if self.logging_methods != '__all__' and request.method not in self.logging_methods:
            super(LoggingMixin, self).initial(request, *args, **kwargs)
            return None

        # get data dict
        try:
            data_dict = request.data.dict()
        except AttributeError:  # if already a dict, can't dictify
            data_dict = request.data
        except UnsupportedMediaType:
            data_dict = None

        # get IP
        ipaddr = request.META.get("HTTP_X_FORWARDED_FOR", None)
        if ipaddr:
            # X_FORWARDED_FOR returns client1, proxy1, proxy2,...
            ipaddr = [x.strip() for x in ipaddr.split(",")][0]
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

        # regular initial, including auth check
        super(LoggingMixin, self).initial(request, *args, **kwargs)

        # add user to log after auth
        user = request.user
        if user.is_anonymous():
            user = None
        self.request.log.user = user
        self.request.log.save()

    def handle_exception(self, exc):
        # basic handling
        response = super(LoggingMixin, self).handle_exception(exc)

        # log error
        self.request.log.errors = traceback.format_exc()
        self.request.log.status_code = response.status_code
        self.request.log.save()

        # return
        return response

    def finalize_response(self, request, response, *args, **kwargs):
        # regular finalize response
        response = super(LoggingMixin, self).finalize_response(request, response, *args, **kwargs)

        # check if request method is being logged
        if self.logging_methods != '__all__' and request.method not in self.logging_methods:
            return response

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
