from .base_mixins import BaseLoggingMixin
from .elastic_client import ElasticClient
from .models import APIRequestLog


class LoggingMixin(BaseLoggingMixin):
    def handle_log(self):
        """
        Hook to define what happens with the log.

        Defaults on saving the data on the db.
        """
        if self.elasticsearch_enabled:
            elastic = ElasticClient()
            elastic.add_api_log(self.log)
        else:
            APIRequestLog(**self.log).save()


class LoggingErrorsMixin(LoggingMixin):
    """
    Log only errors
    """

    def should_log(self, request, response):
        return response.status_code >= 400
