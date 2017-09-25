
from django.utils.deprecation import MiddlewareMixin
from .mixins import LoggingMixin


from rest_framework.views import APIView


class DrfTrackingMiddleware(MiddlewareMixin):
    """Log Every Activity of every Request

    """
    drf_logging = LoggingMixin()

    def _convert_django_request_to_drf_request_object(self, request):
        """convert Django `httpRequest` object into DRF request object

        :param request: Django Http Request Object
        :return: DRF request object
        """
        return APIView().initialize_request(request)

    def process_request(self, request):
        # Don;t log in case of superuser
        if request.user.is_superuser:
            return
        rq = self._convert_django_request_to_drf_request_object(request)
        self.drf_logging.initial(rq, middleware=True)

    def process_exception(self, request, exception, *args, **kwargs):
        """
        """
        # Don;t log in case of superuser

        if request.user.is_superuser:
            return exception
        rq = self._convert_django_request_to_drf_request_object(request)

        self.drf_logging.handle_excption(rq, exception, middleware=True)
        return exception

    def process_response(self, request, response):
        # Don;t log in case of superuser
        if request.user.is_superuser:
            return response

        rq = self._convert_django_request_to_drf_request_object(request)
        self.drf_logging.finalize_response(rq, response, middleware=True)
        return response
