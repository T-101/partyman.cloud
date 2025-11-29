from django.urls import path
from request.views import LandingPageView, RequestIndexView, SuccessView, ActivationView

app_name = "request"

urlpatterns = [
    path('', LandingPageView.as_view(), name='landing_page'),
    path('request/', RequestIndexView.as_view(), name='index'),
    path('success/', SuccessView.as_view(), name='success'),
    path('activation/<int:pk>/', ActivationView.as_view(), name='activation')
]
