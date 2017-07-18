import re
from .models import APIRequestLog
from django.utils.timezone import now
import traceback


class BaseLoggingMixin(object):
    logging_methods = '__all__'

    """Mixin to log requests"""
    def initial(self, request, *args, **kwargs):
        # get IP
        ipaddr = request.META.get("HTTP_X_FORWARDED_FOR", None)
        if ipaddr:
            # X_FORWARDED_FOR returns client1, proxy1, proxy2,...
            ipaddr = [x.strip() for x in ipaddr.split(",")][0]
        else:
            ipaddr = request.META.get("REMOTE_ADDR", "")

        # get view
        view_name = ''
        try:
            method = request.method.lower()
            attributes = getattr(self, method)
            view_name = (type(attributes.__self__).__module__ + '.' +
                         type(attributes.__self__).__name__)
        except Exception:
            pass

        # get the method of the view
        if hasattr(self, 'action'):
            view_method = self.action if self.action else ''
        else:
            view_method = method.lower()

        # create log
        self.request.log = APIRequestLog(
            requested_at=now(),
            path=request.path,
            view=view_name,
            view_method=view_method,
            remote_addr=ipaddr,
            host=request.get_host(),
            method=request.method,
            query_params=_clean_data(request.query_params.dict()),
        )

        # regular initial, including auth check
        super(BaseLoggingMixin, self).initial(request, *args, **kwargs)

        # add user to log after auth
        user = request.user
        if user.is_anonymous():
            user = None
        self.request.log.user = user

        # get data dict
        try:
            # Accessing request.data *for the first time* parses the request body, which may raise
            # ParseError and UnsupportedMediaType exceptions. It's important not to swallow these,
            # as (depending on implementation details) they may only get raised this once, and
            # DRF logic needs them to be raised by the view for error handling to work correctly.
            self.request.log.data = _clean_data(self.request.data.dict())
        except AttributeError:  # if already a dict, can't dictify
            self.request.log.data = _clean_data(self.request.data)

    def handle_exception(self, exc):
        # basic handling
        response = super(BaseLoggingMixin, self).handle_exception(exc)

        # log error
        if hasattr(self.request, 'log'):
            self.request.log.errors = traceback.format_exc()

        # return
        return response

    def finalize_response(self, request, response, *args, **kwargs):
        # regular finalize response
        response = super(BaseLoggingMixin, self).finalize_response(request, response, *args, **kwargs)

        # check if request is being logged
        if not hasattr(self.request, 'log'):
            return response

        # compute response time
        response_timedelta = now() - self.request.log.requested_at
        response_ms = int(response_timedelta.total_seconds() * 1000)

        # save to log
        if (self._should_log(request, response)):
            self.request.log.response = response.rendered_content
            self.request.log.status_code = response.status_code
            self.request.log.response_ms = response_ms
            try:
                self.request.log.save()
            except:
                # ensure that a DB error doesn't prevent API call to continue as expected
                pass

        # return
        return response

    def _should_log(self, request, response):
        """
        Method that should return True if this request should be logged.
        By default, check if the request method is in logging_methods.
        """
        return self.logging_methods == '__all__' or request.method in self.logging_methods


class LoggingMixin(BaseLoggingMixin):
    pass


class LoggingErrorsMixin(BaseLoggingMixin):
    """
    Log only errors
    """
    def _should_log(self, request, response):
        return response.status_code >= 400


def _clean_data(data):
    """
    Clean a dictionary of data of potentially sensitive info before
    sending to the database.
    Function based on the "_clean_credentials" function of django
    (django/django/contrib/auth/__init__.py)
    """
    SENSITIVE_DATA = re.compile('api|token|key|secret|password|signature', re.I)
    CLEANSED_SUBSTITUTE = '********************'
    for key in data:
        if SENSITIVE_DATA.search(key):
            data[key] = CLEANSED_SUBSTITUTE
    return data
