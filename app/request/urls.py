from django.urls import path
from request.views import IndexView, SuccessView

app_name = "request"

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('success/', SuccessView.as_view(), name='success'),
]
