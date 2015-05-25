from django.contrib.auth.models import User
from rest_framework import generics, authentication
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.response import Response
from rest_framework_tracking.models import APIRequestLog
from rest_framework_tracking.mixins import LoggingMixin
import pytest


pytestmark = pytest.mark.django_db


class MockNoLoggingView(generics.GenericAPIView):
    def get(self, request):
        return Response('no logging')


class MockLoggingView(LoggingMixin, generics.GenericAPIView):
    def get(self, request):
        return Response('with logging')


class MockAuthLoggingView(LoggingMixin, generics.GenericAPIView):
    authentication_classes = (authentication.SessionAuthentication,)

    def get(self, request):
        return Response('with logging')


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

    def test_log_anon_user(self):
        MockLoggingView.as_view()(self.request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.user, None)

    def test_log_auth_user(self):
        # set up request with token
        User.objects.create_user(username='myname', password='secret')
        user = User.objects.get(username='myname')
        request = APIRequestFactory().get('/test')
        force_authenticate(request, user=user)

        MockLoggingView.as_view()(request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.user, user)

    def test_params(self):
        request = APIRequestFactory().get('/test?p1=a&another=2')

        MockLoggingView.as_view()(request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.query_params, str({u'p1': u'a', u'another': u'2'}))
