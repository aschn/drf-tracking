from rest_framework import serializers
from rest_framework_tracking.models import APIRequestLog


class ApiRequestLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = APIRequestLog
        fields = '__all__'
