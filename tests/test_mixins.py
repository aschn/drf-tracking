# coding=utf-8
from __future__ import absolute_import

import pytest
import ast
import datetime
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.test.utils import override_settings
from flaky import flaky
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework_tracking.mixins import BaseLoggingMixin
from rest_framework_tracking.models import APIRequestLog

try:
    import mock
except Exception:
    from unittest import mock

from .views import MockLoggingView

pytestmark = pytest.mark.django_db


@override_settings(ROOT_URLCONF='tests.urls')
class TestLoggingMixin(APITestCase):

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

    @flaky
    def test_log_time_fast(self):
        self.client.get('/logging')
        log = APIRequestLog.objects.first()

        # response time is very short
        self.assertLessEqual(log.response_ms, 20)

        # request_at is time of request, not response
        threshold = 0.002
        saved_delay = (now() - log.requested_at).total_seconds()
        self.assertAlmostEqual(threshold, saved_delay, 2)

    def test_log_time_slow(self):
        self.client.get('/slow-logging')
        log = APIRequestLog.objects.first()

        # response time is longer than 1000 milliseconds
        self.assertGreaterEqual(log.response_ms, 1000)

        # request_at is time of request, not response
        self.assertGreaterEqual((now() - log.requested_at).total_seconds(), 1)

    def test_logging_explicit(self):
        self.client.get('/explicit-logging')
        self.client.post('/explicit-logging')
        self.assertEqual(APIRequestLog.objects.all().count(), 1)

    def test_custom_check_logging(self):
        self.client.get('/custom-check-logging')
        self.client.post('/custom-check-logging')
        self.assertEqual(APIRequestLog.objects.all().count(), 1)

    def test_custom_check_logging_deprecated(self):
        self.client.get('/custom-check-logging-deprecated')
        self.client.post('/custom-check-logging-deprecated')
        self.assertEqual(APIRequestLog.objects.all().count(), 1)

    def test_custom_check_logging_with_logging_methods_fail(self):
        """Custom `should_log` does not respect logging_methods."""
        self.client.get('/custom-check-logging-methods-fail')
        self.client.post('/custom-check-logging-methods-fail')
        self.assertEqual(APIRequestLog.objects.all().count(), 2)

    def test_custom_check_logging_with_logging_methods(self):
        """Custom `should_log` respect logging_methods."""
        self.client.get('/custom-check-logging-methods')
        self.client.post('/custom-check-logging-methods')
        self.assertEqual(APIRequestLog.objects.all().count(), 0)

    def test_errors_logging(self):
        self.client.get('/errors-logging')
        self.client.post('/errors-logging')
        self.assertEqual(APIRequestLog.objects.all().count(), 1)

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
        self.assertEqual(ast.literal_eval(log.query_params), {u'p1': u'a', u'another': u'2'})

    def test_log_params_cleaned(self):
        self.client.get('/logging', {'password': '1234', 'key': '12345', 'secret': '123456'})
        log = APIRequestLog.objects.first()
        self.assertEqual(ast.literal_eval(log.query_params), {
                         u'password': BaseLoggingMixin.CLEANED_SUBSTITUTE,
                         u'key': BaseLoggingMixin.CLEANED_SUBSTITUTE,
                         u'secret': BaseLoggingMixin.CLEANED_SUBSTITUTE})

    def test_log_data_empty(self):
        """Default payload is string {}"""
        self.client.post('/logging')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.data, str({}))

    def test_log_data_json(self):
        self.client.post('/logging', {'val': 1, 'val2': [{'a': 'b'}]}, format='json')
        log = APIRequestLog.objects.first()
        expected_data = frozenset({  # keys could be either way round
            str({u'val': 1, u'val2': [{u'a': u'b'}]}),
            str({u'val2': [{u'a': u'b'}], u'val': 1}),
        })
        self.assertIn(log.data, expected_data)

    def test_log_list_data_json(self):
        self.client.post('/logging', [1, 2, {'k1': 1, 'k2': 2}, {'k3': 3}], format='json')

        log = APIRequestLog.objects.first()
        expected_data = str([
            1, 2, {u'k1': 1, u'k2': 2}, {u'k3': 3},
        ])
        self.assertEqual(log.data, expected_data)

    def test_log_data_json_cleaned(self):
        self.client.post('/logging', {'password': '123456', 'val2': [{'val': 'b'}]},
                         format='json')
        log = APIRequestLog.objects.first()
        expected_data = frozenset({  # keys could be either way round
            str({u'password': BaseLoggingMixin.CLEANED_SUBSTITUTE,
                u'val2': [{u'val': u'b'}]}),
            str({u'val2': [{u'val': u'b'}],
                u'password': BaseLoggingMixin.CLEANED_SUBSTITUTE}),
        })
        self.assertIn(log.data, expected_data)

    def test_log_data_json_cleaned_nested(self):
        self.client.post('/logging', {'password': '123456', 'val2': [{'api': 'b'}]},
                         format='json')
        log = APIRequestLog.objects.first()
        expected_data = frozenset({  # keys could be either way round
            str({u'password': BaseLoggingMixin.CLEANED_SUBSTITUTE,
                u'val2': [{u'api': BaseLoggingMixin.CLEANED_SUBSTITUTE}]}),
            str({u'val2': [{u'api': BaseLoggingMixin.CLEANED_SUBSTITUTE}],
                u'password': BaseLoggingMixin.CLEANED_SUBSTITUTE}),
        })
        self.assertIn(log.data, expected_data)

    def test_log_data_json_cleaned_nested_syntax_error(self):
        self.client.post('/logging', {'password': '@', 'val2': [{'api': 'b'}]},
                         format='json')
        log = APIRequestLog.objects.first()
        expected_data = frozenset({  # keys could be either way round
            str({u'password': BaseLoggingMixin.CLEANED_SUBSTITUTE,
                u'val2': [{u'api': BaseLoggingMixin.CLEANED_SUBSTITUTE}]}),
            str({u'val2': [{u'api': BaseLoggingMixin.CLEANED_SUBSTITUTE}],
                u'password': BaseLoggingMixin.CLEANED_SUBSTITUTE}),
        })
        self.assertIn(log.data, expected_data)

    def test_log_exact_match_params_cleaned(self):
        self.client.get('/logging', {'api': '1234', 'capitalized': '12345', 'keyword': '123456'})
        log = APIRequestLog.objects.first()
        self.assertEqual(ast.literal_eval(log.query_params), {
                         u'api': BaseLoggingMixin.CLEANED_SUBSTITUTE,
                         u'capitalized': '12345',
                         u'keyword': '123456'})

    def test_log_params_cleaned_from_personal_list(self):
        self.client.get('/sensitive-fields-logging',
                        {'api': '1234', 'capitalized': '12345', 'my_field': '123456'})
        log = APIRequestLog.objects.first()
        self.assertEqual(ast.literal_eval(log.query_params), {
                         u'api': BaseLoggingMixin.CLEANED_SUBSTITUTE,
                         u'capitalized': '12345',
                         u'my_field': BaseLoggingMixin.CLEANED_SUBSTITUTE})

    def test_log_params_cleaned_from_personal_list_nested(self):
        self.client.get('/sensitive-fields-logging',
                        {'api': '1234', 'var1': {'api': '4321'}})
        log = APIRequestLog.objects.first()
        self.assertEqual(ast.literal_eval(log.query_params), {
                         u'api': BaseLoggingMixin.CLEANED_SUBSTITUTE,
                         u'var1': {u'api': BaseLoggingMixin.CLEANED_SUBSTITUTE}
                         })

    def test_invalid_cleaned_substitute_fails(self):
        with self.assertRaises(AssertionError):
            self.client.get('/invalid-cleaned-substitute-logging')

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
        self.assertIn('Traceback', log.errors)

    def test_log_request_500_error(self):
        self.client.get('/500-error-logging')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.status_code, 500)
        self.assertIn('response', log.response)
        self.assertIn('Traceback', log.errors)

    def test_log_request_415_error(self):
        content_type = 'text/plain'
        self.client.post('/415-error-logging', {}, content_type=content_type)
        log = APIRequestLog.objects.first()
        self.assertEqual(log.status_code, 415)
        self.assertIn('Unsupported media type', log.response)

    def test_log_view_name_api_view(self):
        self.client.get('/no-view-log')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.view, 'tests.views.MockNameAPIView')

    def test_no_log_view_name(self):
        self.client.post('/view-log')
        log = APIRequestLog.objects.first()
        self.assertIsNone(log.view)

    def test_log_view_name_generic_viewset(self):
        self.client.get('/view-log')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.view, 'tests.views.MockNameViewSet')

    def test_log_view_method_name_api_view(self):
        self.client.get('/no-view-log')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.view_method, 'get')

    def test_no_log_view_method_name(self):
        self.client.post('/view-log')
        log = APIRequestLog.objects.first()
        self.assertIsNone(log.view_method)

    def test_log_view_method_name_generic_viewset(self):
        self.client.get('/view-log')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.view_method, 'list')

    def test_log_request_body_parse_error(self):
        content_type = 'application/json'
        self.client.post('/400-body-parse-error-logging', 'INVALID JSON', content_type=content_type)
        log = APIRequestLog.objects.first()
        self.assertEqual(log.status_code, 400)
        self.assertEqual(log.data, 'INVALID JSON')
        self.assertIn('parse error', log.response)

    @mock.patch('rest_framework_tracking.models.APIRequestLog.save')
    def test_log_doesnt_prevent_api_call_if_log_save_fails(self, mock_apirequestlog_save):
        mock_apirequestlog_save.side_effect = Exception('db failure')
        response = self.client.get('/logging')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(APIRequestLog.objects.all().count(), 0)

    @mock.patch('rest_framework_tracking.base_mixins.now')
    def test_log_doesnt_fail_with_negative_response_ms(self, mock_now):
        mock_now.side_effect = [
            datetime.datetime(2017, 12, 1, 10, 0, 10),
            datetime.datetime(2017, 12, 1, 10)
        ]
        self.client.get('/logging')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.response_ms, 0)

    def test_custom_log_handler(self):
            self.client.get('/custom-log-handler')
            self.client.post('/custom-log-handler')
            self.assertEqual(APIRequestLog.objects.all().count(), 1)
