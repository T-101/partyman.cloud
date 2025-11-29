from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView, ListView
from django.utils import timezone

from request.forms import RequestForm, ActivationForm
from request.helpers import get_cloudflare_dns_records, create_cloudflare_dns_entry, create_upcloud_server, \
    delete_cloudflare_dns_entry, stop_upcloud_server, delete_upcloud_server
from request.models import Request, PortfolioItem


class LandingPageView(ListView):
    template_name = "landingpage/index.html"
    model = PortfolioItem

    def get_queryset(self):
        return self.model.objects.filter(visible=True).order_by("sort_order")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["timestamp"] = timezone.now()
        return ctx


class RequestIndexView(CreateView):
    template_name = "request/index.html"
    model = Request
    form_class = RequestForm
    success_url = reverse_lazy('request:success')


class SuccessView(TemplateView):
    template_name = "request/success.html"


class ActivationView(UpdateView):
    template_name = "request/activation.html"
    model = Request
    form_class = ActivationForm
    success_url = reverse_lazy('request:success')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'approved': self.get_object().is_approved})
        kwargs.update({'deactivated': bool(self.get_object().deactivated)})
        return kwargs

    def form_valid(self, form):
        print("Deactivate" in self.request.POST["submit"])
        if "Deactivate" in self.request.POST["submit"]:
            stop_upcloud_server(form.instance)
            delete_cloudflare_dns_entry(form.instance.cloudflare_zone, form.instance.cloudflare_dns_record_id)
            delete_upcloud_server(form.instance)
        else:
            # print(type(form.instance), vars(form.instance))
            domain = form.instance.domain + "." + form.instance.cloudflare_zone.name
            if domain in [record.name for record in get_cloudflare_dns_records(form.instance.cloudflare_zone)]:
                form.add_error('domain', f"Domain {domain} already exists")
                return self.form_invalid(form)

            server_id, server_address = create_upcloud_server(form.instance)
            if not server_id or not server_address:
                form.add_error(None, "Failed to create UpCloud server")
                return self.form_invalid(form)
            cf_dns_id = create_cloudflare_dns_entry(form.instance.cloudflare_zone, form.instance.domain, server_address)
            form.instance.cloudflare_dns_record_id = cf_dns_id
            form.instance.is_approved = True

        return super().form_valid(form)
