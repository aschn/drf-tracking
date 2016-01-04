from django.contrib.auth.models import User
from django.utils.timezone import now
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework_tracking.models import APIRequestLog
from rest_framework.authtoken.models import Token
from views import MockLoggingView
import pytest


pytestmark = pytest.mark.django_db


class TestLoggingMixin(APITestCase):

    urls = 'tests.urls'

    def test_nologging_no_log_created(self):
        self.client.get('/no-logging')
        self.assertEqual(APIRequestLog.objects.all().count(), 0)

    def test_logging_creates_log(self):
        self.client.get('/logging')
        self.assertEqual(APIRequestLog.objects.all().count(), 1)

    def test_log_path(self):
        self.client.get('/logging')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.path, '/logging')

    def test_log_ip_remote(self):
        request = APIRequestFactory().get('/logging')
        request.META['REMOTE_ADDR'] = '127.0.0.9'

        MockLoggingView.as_view()(request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.remote_addr, '127.0.0.9')

    def test_log_ip_xforwarded(self):
        request = APIRequestFactory().get('/logging')
        request.META['HTTP_X_FORWARDED_FOR'] = '127.0.0.8'

        MockLoggingView.as_view()(request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.remote_addr, '127.0.0.8')

    def test_log_host(self):
        self.client.get('/logging')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.host, 'testserver')

    def test_log_method(self):
        self.client.get('/logging')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.method, 'GET')

    def test_log_status(self):
        self.client.get('/logging')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.status_code, 200)

    def test_log_time_fast(self):
        self.client.get('/logging')
        log = APIRequestLog.objects.first()

        # response time is very short
        self.assertLessEqual(log.response_ms, 7)

        # request_at is time of request, not response
        self.assertGreaterEqual((now() - log.requested_at).total_seconds(), 0.002)

    def test_log_time_slow(self):
        self.client.get('/slow-logging')
        log = APIRequestLog.objects.first()

        # response time is longer than 1000 milliseconds
        self.assertGreaterEqual(log.response_ms, 1000)

        # request_at is time of request, not response
        self.assertGreaterEqual((now() - log.requested_at).total_seconds(), 1)

    def test_log_anon_user(self):
        self.client.get('/logging')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.user, None)

    def test_log_auth_user(self):
        # set up active user
        User.objects.create_user(username='myname', password='secret')
        user = User.objects.get(username='myname')

        # set up request with auth
        self.client.login(username='myname', password='secret')
        self.client.get('/session-auth-logging')

        # test
        log = APIRequestLog.objects.first()
        self.assertEqual(log.user, user)

    def test_log_auth_inactive_user(self):
        # set up inactive user with token
        user = User.objects.create_user(username='myname', password='secret')
        token = Token.objects.create(user=user)
        token_header = 'Token %s' % token.key
        user.is_active = False
        user.save()

        # force login because regular client.login doesn't work for inactive users
        self.client.get('/token-auth-logging',
                        HTTP_AUTHORIZATION=token_header)

        # test
        log = APIRequestLog.objects.first()
        self.assertIsNone(log.user)
        self.assertIn("User inactive or deleted", log.response)

    def test_log_unauth_fails(self):
        # set up request without auth
        self.client.logout()
        self.client.get('/session-auth-logging')

        # test
        log = APIRequestLog.objects.first()
        self.assertEqual(log.response, '{"detail":"Authentication credentials were not provided."}')

    def test_log_params(self):
        self.client.get('/logging', {'p1': 'a', 'another': '2'})
        log = APIRequestLog.objects.first()
        self.assertEqual(log.query_params, str({u'p1': u'a', u'another': u'2'}))

    def test_log_data_empty(self):
        """Default payload is string {}"""
        self.client.post('/logging')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.data, str({}))

    def test_log_data_json(self):
        self.client.post('/logging', {'key': 1, 'key2': [{'a': 'b'}]}, format='json')
        log = APIRequestLog.objects.first()
        expected_data = {u'key': 1, u'key2': [{u'a': u'b'}]}
        self.assertEqual(log.data, str(expected_data))

    def test_log_text_response(self):
        self.client.get('/logging')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.response, u'"with logging"')

    def test_log_json_get_response(self):
        self.client.get('/json-logging')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.response, u'{"get":"response"}')

    def test_log_json_post_response(self):
        self.client.post('/json-logging', {}, format='json')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.response, u'{"post":"response"}')

    def test_log_status_validation_error(self):
        self.client.get('/validation-error-logging')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.status_code, 400)
        self.assertEqual(log.response, u'["bad input"]')

    def test_log_request_404_error(self):
        self.client.get('/404-error-logging')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.status_code, 404)
        self.assertIn('Not found', log.response)
