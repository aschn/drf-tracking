import ast
from .models import APIRequestLog
from django.utils.timezone import now
import traceback


class BaseLoggingMixin(object):
    SENSITIVE_FIELDS = {'api', 'token', 'key', 'secret', 'password', 'signature'}
    CLEANED_SUBSTITUTE = '********************'

    logging_methods = '__all__'
    sensitive_fields = {}

    """Mixin to log requests"""
    def initial(self, request, *args, **kwargs):
        # get IP
        ipaddr = request.META.get("HTTP_X_FORWARDED_FOR", None)
        if ipaddr:
            # X_FORWARDED_FOR returns client1, proxy1, proxy2,...
            ipaddr = ipaddr.split(",")[0].strip()
        else:
            ipaddr = request.META.get("REMOTE_ADDR", "")

        # get view
        method = request.method.lower()
        try:
            attributes = getattr(self, method)
            view_name = (type(attributes.__self__).__module__ + '.' +
                         type(attributes.__self__).__name__)
        except AttributeError:
            view_name = ''

        # get the method of the view
        if hasattr(self, 'action'):
            view_method = self.action if self.action else ''
        else:
            view_method = method

        # create log
        self.request.log = APIRequestLog(
            requested_at=now(),
            path=request.path,
            view=view_name,
            view_method=view_method,
            remote_addr=ipaddr,
            host=request.get_host(),
            method=request.method,
            data=request.body,
            query_params=self._clean_data(request.query_params.dict()),
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
            self.request.log.data = self._clean_data(self.request.data.dict())
        except AttributeError:  # if already a dict, can't dictify
            self.request.log.data = self._clean_data(self.request.data)

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

        # save to log
        if (self._should_log(request, response)):
            # compute response time
            response_timedelta = now() - self.request.log.requested_at
            response_ms = int(response_timedelta.total_seconds() * 1000)

            self.request.log.response = response.rendered_content
            self.request.log.status_code = response.status_code
            self.request.log.response_ms = response_ms
            try:
                self.request.log.save()
            except Exception:
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

    def _clean_data(self, data):
        """
        Clean a dictionary of data of potentially sensitive info before
        sending to the database.
        Function based on the "_clean_credentials" function of django
        (https://github.com/django/django/blob/stable/1.11.x/django/contrib/auth/__init__.py#L50)

        Fields defined by django are by default cleaned with this function

        You can define your own sensitive fields in your view by defining a set
        eg: sensitive_fields = {'field1', 'field2'}
        """
        if isinstance(data, list):
            return [self._clean_data(d) for d in data]

        if isinstance(data, dict):
            data = dict(data)

            if self.sensitive_fields:
                self.SENSITIVE_FIELDS = self.SENSITIVE_FIELDS | {field.lower() for field in self.sensitive_fields}

            for key, value in data.items():
                try:
                    value = ast.literal_eval(value)
                except ValueError:
                    pass
                if isinstance(value, list) or isinstance(value, dict):
                    data[key] = self._clean_data(value)
                if key.lower() in self.SENSITIVE_FIELDS:
                    data[key] = self.CLEANED_SUBSTITUTE
        return data


class LoggingMixin(BaseLoggingMixin):
    pass


class LoggingErrorsMixin(BaseLoggingMixin):
    """
    Log only errors
    """
    def _should_log(self, request, response):
        return response.status_code >= 400
