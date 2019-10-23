from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_tracking.models import APIRequestLog


class ApiRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIRequestLog
        fields = ('view',)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
