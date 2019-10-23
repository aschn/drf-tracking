# coding=utf-8
from __future__ import absolute_import
from . import views as test_views
from rest_framework.routers import DefaultRouter
import django

from django.conf.urls import url

if django.VERSION[0] == 1:
    from django.conf.urls import include
else:
    from django.urls import include


router = DefaultRouter()
router.register(r'user', test_views.MockUserViewSet)

urlpatterns = [
    url(r'^no-logging$', test_views.MockNoLoggingView.as_view()),
    url(r'^logging$', test_views.MockLoggingView.as_view()),
    url(r'^logging-exception$', test_views.MockLoggingView.as_view()),
    url(r'^slow-logging$', test_views.MockSlowLoggingView.as_view()),
    url(r'^explicit-logging$', test_views.MockExplicitLoggingView.as_view()),
    url(r'^sensitive-fields-logging$', test_views.MockSensitiveFieldsLoggingView.as_view()),
    url(r'^invalid-cleaned-substitute-logging$', test_views.MockInvalidCleanedSubstituteLoggingView.as_view()),
    url(r'^custom-check-logging-deprecated$', test_views.MockCustomCheckLoggingViewDeprecated.as_view()),
    url(r'^custom-check-logging$', test_views.MockCustomCheckLoggingView.as_view()),
    url(r'^custom-check-logging-methods$', test_views.MockCustomCheckLoggingWithLoggingMethodsView.as_view()),
    url(r'^custom-check-logging-methods-fail$', test_views.MockCustomCheckLoggingWithLoggingMethodsFailView.as_view()),
    url(r'^custom-log-handler$', test_views.MockCustomLogHandlerView.as_view()),
    url(r'^errors-logging$', test_views.MockLoggingErrorsView.as_view()),
    url(r'^session-auth-logging$', test_views.MockSessionAuthLoggingView.as_view()),
    url(r'^token-auth-logging$', test_views.MockTokenAuthLoggingView.as_view()),
    url(r'^json-logging$', test_views.MockJSONLoggingView.as_view()),
    url(r'^multipart-logging$', test_views.MockMultipartLoggingView.as_view()),
    url(r'^streaming-logging$', test_views.MockStreamingLoggingView.as_view()),
    url(r'^validation-error-logging$', test_views.MockValidationErrorLoggingView.as_view()),
    url(r'^404-error-logging$', test_views.Mock404ErrorLoggingView.as_view()),
    url(r'^500-error-logging$', test_views.Mock500ErrorLoggingView.as_view()),
    url(r'^415-error-logging$', test_views.Mock415ErrorLoggingView.as_view()),
    url(r'^no-view-log$', test_views.MockNameAPIView.as_view()),
    url(r'^view-log$', test_views.MockNameViewSet.as_view({'get': 'list'})),
    url(r'^400-body-parse-error-logging$', test_views.Mock400BodyParseErrorLoggingView.as_view()),
    url(r'', include(router.urls))
]
