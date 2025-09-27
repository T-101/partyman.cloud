from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from request.forms import RequestForm
from request.models import Request


class IndexView(CreateView):
    template_name = "request/index.html"
    model = Request
    form_class = RequestForm
    success_url = reverse_lazy('request:success')


class SuccessView(TemplateView):
    template_name = "request/success.html"
