from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.timezone import now
from rest_framework_tracking.models import APIRequestLog
import pytest


pytestmark = pytest.mark.django_db


class TestAPIRequestLog(TestCase):
    def setUp(self):
        username = 'api_user'
        password = 'apipw'
        self.user = User.objects.create_user(username, 'api_user@example.com', password)
        self.ip = '127.0.0.1'

    def test_create_anon(self):
        log = APIRequestLog.objects.create(remote_addr=self.ip, requested_at=now())
        self.assertIsNone(log.user)

    def test_create_auth(self):
        log = APIRequestLog.objects.create(user=self.user, remote_addr=self.ip,
                                           requested_at=now())
        self.assertEqual(log.user, self.user)

    def test_create_timestamp(self):
        before = now()
        log = APIRequestLog.objects.create(remote_addr=self.ip, requested_at=now())
        after = now()

        self.assertLess(log.requested_at, after)
        self.assertGreater(log.requested_at, before)

    def test_path(self):
        log = APIRequestLog.objects.create(path='/test', remote_addr=self.ip, requested_at=now())
        self.assertEqual(log.path, '/test')

    def test_remote_addr(self):
        log = APIRequestLog.objects.create(remote_addr='127.0.0.9', requested_at=now())
        self.assertEqual(log.remote_addr, '127.0.0.9')

    def test_host(self):
        log = APIRequestLog.objects.create(remote_addr=self.ip, host='testserver', requested_at=now())
        self.assertEqual(log.host, 'testserver')

    def test_method(self):
        log = APIRequestLog.objects.create(remote_addr=self.ip, method='GET', requested_at=now())
        self.assertEqual(log.method, 'GET')

    def test_params(self):
        log = APIRequestLog.objects.create(remote_addr=self.ip,
                                           query_params={'test1': 1},
                                           requested_at=now())
        self.assertEqual(log.query_params, {'test1': 1})

    def test_default_response_ms(self):
        log = APIRequestLog.objects.create(remote_addr=self.ip, requested_at=now())
        self.assertEqual(log.response_ms, 0)
