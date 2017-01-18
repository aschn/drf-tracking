from django.shortcuts import get_list_or_404
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework_tracking.mixins import LoggingMixin
from rest_framework_tracking.models import APIRequestLog
import time


class MockNoLoggingView(APIView):
    def get(self, request):
        return Response('no logging')


class MockLoggingView(LoggingMixin, APIView):
    def get(self, request):
        return Response('with logging')


class MockSlowLoggingView(LoggingMixin, APIView):
    def get(self, request):
        time.sleep(1)
        return Response('with logging')


class MockExplicitLoggingView(LoggingMixin, APIView):
    logging_methods = ['POST']

    def get(self, request):
        return Response('no logging')

    def post(self, request):
        return Response('with logging')


class MockSessionAuthLoggingView(LoggingMixin, APIView):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response('with session auth logging')


class MockTokenAuthLoggingView(LoggingMixin, APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response('with token auth logging')


class MockJSONLoggingView(LoggingMixin, APIView):
    def get(self, request):
        return Response({'get': 'response'})

    def post(self, request):
        return Response({'post': 'response'})


class MockValidationErrorLoggingView(LoggingMixin, APIView):
    def get(self, request):
        raise serializers.ValidationError('bad input')


class Mock404ErrorLoggingView(LoggingMixin, APIView):
    def get(self, request):
        empty_qs = APIRequestLog.objects.none()
        return get_list_or_404(empty_qs)


class Mock415ErrorLoggingView(LoggingMixin, APIView):
    def post(self, request):
        return request.data


class Mock400BodyParseErrorLoggingView(LoggingMixin, APIView):
    def post(self, request):
        # raise ParseError for request with mismatched Content-Type and body:
        # (though only if it's the first access to request.data)
        request.data
        return Response('Data processed')
