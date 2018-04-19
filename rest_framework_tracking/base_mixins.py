import ast
import logging
import traceback

from django.db import connection
from django.utils.timezone import now

logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


class BaseLoggingMixin(object):
    """Mixin to log requests"""

    CLEANED_SUBSTITUTE = '********************'

    logging_methods = '__all__'
    sensitive_fields = {}

    def __init__(self, *args, **kwargs):
        assert isinstance(self.CLEANED_SUBSTITUTE, str), 'CLEANED_SUBSTITUTE must be a string.'
        super(BaseLoggingMixin, self).__init__(*args, **kwargs)

    def initial(self, request, *args, **kwargs):
        self.log = {}
        self.log['requested_at'] = now()
        self.log['data'] = request.body

        super(BaseLoggingMixin, self).initial(request, *args, **kwargs)

        try:
            # Accessing request.data *for the first time* parses the request body, which may raise
            # ParseError and UnsupportedMediaType exceptions. It's important not to swallow these,
            # as (depending on implementation details) they may only get raised this once, and
            # DRF logic needs them to be raised by the view for error handling to work correctly.
            data = self.request.data.dict()
        except AttributeError:
            data = self.request.data
        self.log['data'] = data

    def handle_exception(self, exc):
        response = super(BaseLoggingMixin, self).handle_exception(exc)
        self.log['errors'] = traceback.format_exc()

        return response

    def finalize_response(self, request, response, *args, **kwargs):
        response = super(BaseLoggingMixin, self).finalize_response(request, response, *args, **kwargs)

        # Ensure backward compatibility for those using _should_log hook
        should_log = self._should_log if hasattr(self, '_should_log') else self.should_log

        if should_log(request, response):

            self.log.update(
                {
                    'remote_addr': self._get_ip_address(request),
                    'view': self._get_view_name(request),
                    'view_method': self._get_view_method(request),
                    'path': request.path,
                    'host': request.get_host(),
                    'method': request.method,
                    'query_params': self._clean_data(request.query_params.dict()),
                    'user': self._get_user(request),
                    'response_ms': self._get_response_ms(),
                    'response': response.rendered_content if hasattr(response, 'rendered_content') else response.getvalue(),
                    'status_code': response.status_code,
                    'data': self._clean_data(self.log['data'])
                }
            )
            try:
                if not connection.settings_dict.get('ATOMIC_REQUESTS'):
                    self.handle_log()
                elif response.exception and not connection.in_atomic_block or not response.exception:
                    self.handle_log()
                elif response.exception:
                    # respone with exception (HTTP status like: 401, 404, etc)
                    # pointwise disable atomic block for handle log (TransactionManagementError)
                    connection.set_rollback(True)
                    connection.set_rollback(False)
                    self.handle_log()
            except Exception as e:
                # ensure that all exceptions raised by handle_log
                # doesn't prevent API call to continue as expected
                logger.exception('Logging API call raise exception!')

        return response

    def handle_log(self):
        """
        Hook to define what happens with the log.

        Defaults on saving the data on the db.
        """
        raise NotImplementedError

    def _get_ip_address(self, request):
        """Get the remote ip address the request was generated from. """
        ipaddr = request.META.get("HTTP_X_FORWARDED_FOR", None)
        if ipaddr:
            # X_FORWARDED_FOR returns client1, proxy1, proxy2,...
            return ipaddr.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")

    def _get_view_name(self, request):
        """Get view name."""
        method = request.method.lower()
        try:
            attributes = getattr(self, method)
            view_name = (type(attributes.__self__).__module__ + '.' +
                         type(attributes.__self__).__name__)
            return view_name
        except AttributeError:
            return None

    def _get_view_method(self, request):
        """Get view method."""
        if hasattr(self, 'action'):
            return self.action if self.action else None
        return request.method.lower()

    def _get_user(self, request):
        """Get user."""
        user = request.user
        if not user.is_authenticated:
            return None
        return user

    def _get_response_ms(self):
        """
        Get the duration of the request response cycle is milliseconds.
        In case of negative duration 0 is returned.
        """
        response_timedelta = now() - self.log['requested_at']
        response_ms = int(response_timedelta.total_seconds() * 1000)
        return max(response_ms, 0)

    def should_log(self, request, response):
        """
        Method that should return a value that evaluated to True if the request should be logged.
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
            SENSITIVE_FIELDS = {'api', 'token', 'key', 'secret', 'password', 'signature'}

            data = dict(data)
            if self.sensitive_fields:
                SENSITIVE_FIELDS = SENSITIVE_FIELDS | {field.lower() for field in self.sensitive_fields}

            for key, value in data.items():
                try:
                    value = ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    pass
                if isinstance(value, list) or isinstance(value, dict):
                    data[key] = self._clean_data(value)
                if key.lower() in SENSITIVE_FIELDS:
                    data[key] = self.CLEANED_SUBSTITUTE
        return data
