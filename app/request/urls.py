from django.urls import path
from request.views import IndexView, SuccessView, ActivationView

app_name = "request"

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('success/', SuccessView.as_view(), name='success'),
    path('activation/<int:pk>/', ActivationView.as_view(), name='activation')
]
