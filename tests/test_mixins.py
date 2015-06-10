from django.contrib.auth.models import User
from django.utils.timezone import now
from rest_framework.authentication import SessionAuthentication
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework_tracking.models import APIRequestLog
from rest_framework_tracking.mixins import LoggingMixin
import pytest
import time


pytestmark = pytest.mark.django_db


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


class MockAuthLoggingView(LoggingMixin, APIView):
    authentication_classes = (SessionAuthentication,)

    def get(self, request):
        return Response('with logging')


class MockJSONLoggingView(LoggingMixin, APIView):
    def get(self, request):
        return Response({'get': 'response'})

    def post(self, request):
        return Response({'post': 'response'})


class MockErrorLoggingView(LoggingMixin, APIView):
    def get(self, request):
        raise serializers.ValidationError('bad input')


class TestLoggingMixin(APITestCase):
    def setUp(self):
        factory = APIRequestFactory()
        self.path = '/test/'
        self.request = factory.get(self.path)

    def test_nologging_no_log_created(self):
        MockNoLoggingView.as_view()(self.request).render()
        self.assertEqual(APIRequestLog.objects.all().count(), 0)

    def test_logging_creates_log(self):
        MockLoggingView.as_view()(self.request).render()
        self.assertEqual(APIRequestLog.objects.all().count(), 1)

    def test_log_path(self):
        MockLoggingView.as_view()(self.request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.path, self.path)

    def test_log_ip(self):
        self.request.META['REMOTE_ADDR'] = '127.0.0.9'
        MockLoggingView.as_view()(self.request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.remote_addr, '127.0.0.9')

    def test_log_host(self):
        MockLoggingView.as_view()(self.request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.host, 'testserver')

    def test_log_method(self):
        MockLoggingView.as_view()(self.request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.method, 'GET')

    def test_log_status(self):
        MockLoggingView.as_view()(self.request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.status_code, 200)

    def test_log_time_fast(self):
        MockLoggingView.as_view()(self.request).render()
        log = APIRequestLog.objects.first()

        # response time is very short
        self.assertLessEqual(log.response_ms, 1)

        # request_at is time of request, not response
        self.assertGreaterEqual((now() - log.requested_at).total_seconds(), 0.001)

    def test_log_time_slow(self):
        MockSlowLoggingView.as_view()(self.request).render()
        log = APIRequestLog.objects.first()

        # response time is longer than 1000 milliseconds
        self.assertGreaterEqual(log.response_ms, 1000)

        # request_at is time of request, not response
        self.assertGreaterEqual((now() - log.requested_at).total_seconds(), 1)

    def test_log_anon_user(self):
        MockLoggingView.as_view()(self.request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.user, None)

    def test_log_auth_user(self):
        # set up request with auth
        User.objects.create_user(username='myname', password='secret')
        user = User.objects.get(username='myname')
        request = APIRequestFactory().get('/test')
        force_authenticate(request, user=user)

        MockLoggingView.as_view()(request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.user, user)

    def test_log_params(self):
        request = APIRequestFactory().get('/test?p1=a&another=2')

        MockLoggingView.as_view()(request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.query_params, str({u'p1': u'a', u'another': u'2'}))

    def test_log_data_empty(self):
        """Default payload is string {}"""
        request = APIRequestFactory().post('/test')

        MockLoggingView.as_view()(request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.data, str({}))

    def test_log_data_json(self):
        payload = {'key': 1, 'key2': [{'a': 'b'}]}
        request = APIRequestFactory().post('/test', payload, format='json')

        MockLoggingView.as_view()(request).render()
        log = APIRequestLog.objects.first()
        expected_data = {u'key': 1, u'key2': [{u'a': u'b'}]}
        self.assertEqual(log.data, str(expected_data))

    def test_log_text_response(self):
        MockLoggingView.as_view()(self.request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.response, u'"with logging"')

    def test_log_json_get_response(self):
        MockJSONLoggingView.as_view()(self.request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.response, u'{"get":"response"}')

    def test_log_json_post_response(self):
        request = APIRequestFactory().post('/test', {}, format='json')
        MockJSONLoggingView.as_view()(request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.response, u'{"post":"response"}')

    def test_log_status_error(self):
        MockErrorLoggingView.as_view()(self.request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.status_code, 400)
        self.assertEqual(log.response, u'["bad input"]')
