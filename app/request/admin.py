import json

from django import forms
from django.contrib import admin

from .models import Request, UpCloudZone, CloudflareZone, UpCloudPlan, SSHKeys, PortfolioItem, ExternalURL, Testimonial, \
    Email


class ExternalURLInline(admin.TabularInline):
    model = ExternalURL
    extra = 0


class TestimonialInline(admin.TabularInline):
    model = Testimonial
    extra = 0


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'heading', 'sort_order', 'visible']
    inlines = [ExternalURLInline, TestimonialInline]
    list_editable = ['visible', 'sort_order']


@admin.register(ExternalURL)
class ExternalURLAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'url', 'visible']
    list_filter = ['created', 'modified', 'visible']


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'party_name', 'is_approved',
                    'created', 'party_start',
                    'domain', 'cloudflare_zone', 'upcloud_zone', 'activated', 'deactivated']
    list_filter = ['party_start', 'party_end', 'upcloud_zone', 'cloudflare_zone', 'is_approved', 'activated',
                   'deactivated', 'created', 'modified']
    search_fields = ['party_name', 'domain', 'cloudflare_zone', 'upcloud_zone']


@admin.register(UpCloudZone)
class UpCloudZoneAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'visible']
    list_filter = ['created', 'modified', 'visible']
    search_fields = ['name']


@admin.register(UpCloudPlan)
class UpCloudPlanAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description', 'visible']
    list_filter = ['created', 'modified', 'visible']
    search_fields = ['name']


@admin.register(CloudflareZone)
class CloudflareZoneAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'cloudflare_id', 'public', 'visible', 'created', 'modified']
    list_filter = ['created', 'modified', 'public']
    search_fields = ['name']


@admin.register(SSHKeys)
class SSHKeysAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'public_key', 'created')
    readonly_fields = ['created', 'modified']


class PrettyJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, indent, sort_keys, **kwargs):
        super().__init__(*args, indent=2, sort_keys=True, **kwargs)


@admin.register(Email)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'recipients', 'created', 'modified']
    list_filter = ['created', 'modified']
    readonly_fields = ['recipients', 'created', 'modified']
    search_fields = ['recipients', 'text_content', 'html_content']

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        form.base_fields['delivery_status_json'].encoder = PrettyJSONEncoder
        form.base_fields['delivery_status_json'].widget.attrs['disabled'] = "disabled"
        form.base_fields['text_content'].widget.attrs['disabled'] = "disabled"
        form.base_fields['html_content'].widget.attrs['disabled'] = "disabled"
        form.base_fields['delivery_status_json'].widget.attrs['class'] = "vLargeTextField"
        return form
