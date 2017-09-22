import logging
import traceback

from django.conf import settings
from django.utils.timezone import now

from rest_framework_tracking.elastic_client import ElasticClient
from rest_framework_tracking.models import APIRequestLog

logger = logging.getLogger(__name__)


class BaseLoggingMixin(object):
    """Mixin to log requests"""

    logging_methods = '__all__'
    sensitive_fields = {}
    # Internal usage
    log = {
        "requested_at": '',
        "path": '',
        "view": '',
        "view_method": '',
        "remote_addr": '',
        "host": '',
        "method": '',
        "query_params": '',
        "data": '',
        "user": '',
        "response": '',
        "status_code": '',
        "response_ms": '',
        "errors": '',
    }
    # Elastic search config
    elasticsearch_enabled = hasattr(settings, 'DRF_TRACKING_ELASTIC_CONFIG')

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

        # save first part of the information
        self.log['requested_at'] = now()
        self.log['path'] = request.path
        self.log['view'] = view_name
        self.log['view_method'] = view_method
        self.log['remote_addr'] = ipaddr
        self.log['host'] = request.get_host()
        self.log['method'] = request.method
        self.log['query_params'] = self._clean_data(request.query_params.dict())

        # regular initial, including auth check
        super(BaseLoggingMixin, self).initial(request, *args, **kwargs)
        # add user to log after auth
        user = request.user
        if user.is_anonymous():
            user_id = None
        else:
            user_id = user.id
        self.log['user'] = user_id

        # get data dict
        try:
            # Accessing request.data *for the first time* parses the request body, which may raise
            # ParseError and UnsupportedMediaType exceptions. It's important not to swallow these,
            # as (depending on implementation details) they may only get raised this once, and
            # DRF logic needs them to be raised by the view for error handling to work correctly.
            self.log['data'] = self._clean_data(self.request.data.dict())
        except AttributeError:  # if already a dict, can't dictify
            self.log['data'] = self._clean_data(self.request.data)

    def handle_exception(self, exc):
        # basic handling
        response = super(BaseLoggingMixin, self).handle_exception(exc)
        # log error
        if hasattr(self, 'log'):
            self.log['errors'] = traceback.format_exc()

        return response

    def finalize_response(self, request, response, *args, **kwargs):
        # regular finalize response
        response = super(BaseLoggingMixin, self).finalize_response(request, response, *args,
                                                                   **kwargs)

        # check if request is being logged
        if not self.log['requested_at']:
            return response

        # compute response time
        response_timedelta = now() - self.log['requested_at']
        response_ms = int(response_timedelta.total_seconds() * 1000)

        # save to log
        if (self._should_log(request, response)):
            self.log['response'] = response.rendered_content
            self.log['status_code'] = response.status_code
            self.log['response_ms'] = response_ms
            try:
                self._save_log_data(self.log)
            except Exception as e:
                # ensure that a DB error doesn't prevent API call to continue as expected
                logger.exception(e)
                pass

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
        data = dict(data)

        SENSITIVE_FIELDS = {'api', 'token', 'key', 'secret', 'password', 'signature'}
        CLEANED_SUBSTITUTE = '********************'

        if self.sensitive_fields:
            SENSITIVE_FIELDS = SENSITIVE_FIELDS | {field.lower() for field in self.sensitive_fields}

        for key in data:
            if key.lower() in SENSITIVE_FIELDS:
                data[key] = CLEANED_SUBSTITUTE
        return data

    def _save_log_data(self, data):
        """
        Check if options for elasticsearch are configured and save data either in elastic search or
        in the database configured for the django project
        """
        if self.elasticsearch_enabled:
            elastic = ElasticClient()
            elastic.add_api_log(data)
        else:
            apirequest = APIRequestLog(**data)
            apirequest.save()


class LoggingMixin(BaseLoggingMixin):
    pass


class LoggingErrorsMixin(BaseLoggingMixin):
    """
    Log only errors
    """
    def _should_log(self, request, response):
        return response.status_code >= 400
