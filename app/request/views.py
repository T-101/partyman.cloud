from django.db.models import Avg, Case, DateTimeField, DurationField, ExpressionWrapper, F, Value, When, Count
from django.db.models.functions import Coalesce
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView, ListView
from django.utils import timezone

from request.forms import RequestForm, ActivationForm
from request.helpers import get_cloudflare_dns_records, create_cloudflare_dns_entry, create_upcloud_server, \
    delete_cloudflare_dns_entry, stop_upcloud_server, delete_upcloud_server
from request.models import Request, PortfolioItem, AppSettings


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


class ActivationListView(ListView):
    template_name = "request/activation-list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["zones"] = list(Request.objects
                            .values("upcloud_zone__name")
                            .filter(upcloud_zone__name__isnull=False)
                            .annotate(count=Count("upcloud_zone__name")).order_by("-count"))
        ctx["plans"] = list(Request.objects
                            .values("upcloud_plan__name")
                            .filter(upcloud_plan__name__isnull=False)
                            .annotate(count=Count("upcloud_plan__name")).order_by("-count"))
        ctx["average_duration_activated"] = (Request.objects.filter(activated__isnull=False, deactivated__isnull=False)
        .aggregate(
            avg_duration=Avg(
                ExpressionWrapper(F("deactivated") - F("activated"), output_field=DurationField())
            )
        )["avg_duration"])
        return ctx

    def get_queryset(self):
        return Request.objects.prefetch_related("activated_by", "deactivated_by", "upcloud_zone").annotate(
            is_inactive=Case(
                When(activated__isnull=False, deactivated__isnull=True, then=Value(0)),
                default=Value(1),
            ),
            duration_activated=Case(
                When(
                    activated__isnull=False,
                    then=ExpressionWrapper(
                        Coalesce(
                            "deactivated",
                            Value(timezone.now(), output_field=DateTimeField()),
                        ) - F("activated"),
                        output_field=DurationField(),
                    ),
                ),
                default=Value(None, output_field=DurationField()),
            )
        ).order_by("is_inactive", "-party_start")


class ActivationDetailView(UpdateView):
    template_name = "request/activation-detail.html"
    model = Request
    form_class = ActivationForm
    success_url = reverse_lazy('request:success')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'approved': self.get_object().is_approved})
        kwargs.update({'deactivated': bool(self.get_object().deactivated)})
        return kwargs

    def form_valid(self, form):
        settings = AppSettings.load()
        if "Deactivate" in self.request.POST["submit"]:
            request = self.get_object()
            form.instance.cloudflare_zone = request.cloudflare_zone
            form.instance.domain = request.domain
            form.instance.deactivated_by = self.request.user
            form.instance.deactivated = timezone.now()
            if not settings.sandbox_mode:
                stop_upcloud_server(form.instance)
                delete_cloudflare_dns_entry(form.instance.cloudflare_zone, form.instance.cloudflare_dns_record_id)
                delete_upcloud_server(form.instance)
            form.save()
            return HttpResponseRedirect(reverse_lazy("request:activation-list"))
        else:
            # print(type(form.instance), vars(form.instance))
            if not settings.sandbox_mode:
                domain = form.instance.domain + "." + form.instance.cloudflare_zone.name
                if domain in [record.name for record in get_cloudflare_dns_records(form.instance.cloudflare_zone)]:
                    form.add_error('domain', f"Domain {domain} already exists")
                    return self.form_invalid(form)

                server_id, server_address = create_upcloud_server(form.instance)
                if not server_id or not server_address:
                    form.add_error(None, "Failed to create UpCloud server")
                    return self.form_invalid(form)
                cf_dns_id = create_cloudflare_dns_entry(form.instance.cloudflare_zone, form.instance.domain,
                                                        server_address)
                form.instance.cloudflare_dns_record_id = cf_dns_id
            form.instance.is_approved = True
            form.instance.activated_by = self.request.user
            form.instance.activated = timezone.now()

        return super().form_valid(form)
