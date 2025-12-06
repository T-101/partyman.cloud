from django.urls import path
from request.views import LandingPageView, RequestIndexView, SuccessView, ActivationDetailView, ActivationListView

app_name = "request"

urlpatterns = [
    path('', LandingPageView.as_view(), name='landing_page'),
    path('request/', RequestIndexView.as_view(), name='index'),
    path('success/', SuccessView.as_view(), name='success'),
    path('activation/', ActivationListView.as_view(), name="activation-list"),
    path('activation/<int:pk>/', ActivationDetailView.as_view(), name='activation-detail'),
]
