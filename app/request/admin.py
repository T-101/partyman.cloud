from django.contrib import admin

from .models import Request, UpCloudZone, CloudflareZone, UpCloudPlan, SSHKeys, PortfolioItem, ExternalURL, Testimonial


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'heading', 'sort_order', 'visible']


@admin.register(ExternalURL)
class ExternalURLAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'url', 'visible']
    list_filter = ['created', 'modified', 'visible']


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'party_name', 'is_approved',
                    'party_start', 'party_end',
                    'domain', 'cloudflare_zone', 'upcloud_zone', 'activated', 'deactivated']
    list_filter = ['party_start', 'party_end', 'upcloud_zone', 'cloudflare_zone', 'is_approved', 'activated',
                   'deactivated', 'created', 'modified']


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
    list_display = ['id', 'created', 'modified', 'name', 'cloudflare_id', 'public', 'visible']
    list_filter = ['created', 'modified', 'public']
    search_fields = ['name']


@admin.register(SSHKeys)
class SSHKeysAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'public_key')
