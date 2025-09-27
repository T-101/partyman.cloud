import re

from django.db import models
from django.core.exceptions import ValidationError

from django_extensions.db.models import TimeStampedModel


def domain_validator(value):
    if not re.match(r'^[a-z0-9-]+$', value):
        raise ValidationError(
            'Domain can only contain lowercase letters (a-z), numbers (0-9) and hyphens (-).'
        )


class Request(TimeStampedModel):
    party_name = models.CharField(max_length=255)
    party_url = models.URLField(blank=True, null=True, help_text="URL to the party's official website")
    contact_email = models.EmailField(help_text="Contact email for the party organizers")
    party_start = models.DateField()
    party_end = models.DateField()
    domain = models.CharField(max_length=255, validators=[domain_validator],
                              help_text='Subdomain for the instance without the host, usually name of the party. '
                                        'Accepted characters are a-z, 0-9 and hyphen (-). Example: myparty')
    upcloud_zone = models.ForeignKey('UpCloudZone', on_delete=models.CASCADE, related_name='requests',
                                     blank=True, null=True)
    upcloud_plan = models.ForeignKey('UpCloudPlan', on_delete=models.CASCADE, related_name='requests',
                                     blank=True, null=True)

    cloudflare_zone = models.ForeignKey('CloudflareZone', on_delete=models.CASCADE, related_name='requests')
    cloudflare_dns_record_id = models.CharField(max_length=255, blank=True, null=True)
    upcloud_server_id = models.CharField(max_length=255, blank=True, null=True)
    upcloud_server_address = models.GenericIPAddressField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    activated = models.DateTimeField(blank=True, null=True)
    deactivated = models.DateTimeField(blank=True, null=True)


def __str__(self):
    return self.party_name


class UpCloudZone(TimeStampedModel):
    class Meta:
        verbose_name = "UpCloud Zone"
        verbose_name_plural = "UpCloud Zones"

    name = models.CharField(max_length=255)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class UpCloudPlan(TimeStampedModel):
    class Meta:
        verbose_name = "UpCloud Plan"
        verbose_name_plural = "UpCloud Plans"

    name = models.CharField(max_length=255)
    description = models.CharField(blank=True, null=True)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return self.description


class CloudflareZone(TimeStampedModel):
    name = models.CharField(max_length=255)
    cloudflare_id = models.CharField(max_length=255, unique=True)
    public = models.BooleanField(default=False)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SSHKeys(models.Model):
    class Meta:
        verbose_name = "SSH Keys"
        verbose_name_plural = "SSH Keys"
    user = models.CharField(max_length=255)
    public_key = models.TextField()

    def __str__(self):
        return self.user
