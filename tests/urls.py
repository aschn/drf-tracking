from django.conf.urls import url
import views as test_views

urlpatterns = [
    url(r'^no-logging$', test_views.MockNoLoggingView.as_view()),
    url(r'^logging$', test_views.MockLoggingView.as_view()),
    url(r'^slow-logging$', test_views.MockSlowLoggingView.as_view()),
    url(r'^explicit-logging$', test_views.MockExplicitLoggingView.as_view()),
    url(r'^session-auth-logging$', test_views.MockSessionAuthLoggingView.as_view()),
    url(r'^token-auth-logging$', test_views.MockTokenAuthLoggingView.as_view()),
    url(r'^json-logging$', test_views.MockJSONLoggingView.as_view()),
    url(r'^validation-error-logging$', test_views.MockValidationErrorLoggingView.as_view()),
    url(r'^404-error-logging$', test_views.Mock404ErrorLoggingView.as_view()),
]
