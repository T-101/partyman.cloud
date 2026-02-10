import re
from cryptography.fernet import Fernet, InvalidToken

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.core.exceptions import ValidationError
from django.core.cache import cache

from django_extensions.db.models import TimeStampedModel


def domain_validator(value):
    if not re.match(r'^[a-z0-9-]+$', value):
        raise ValidationError(
            'Domain can only contain lowercase letters (a-z), numbers (0-9) and hyphens (-).'
        )


fernet = Fernet(settings.FERNET_ENCRYPTION_KEY)


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def set_cache(self):
        cache.set(self.__class__.__name__, self)

    def save(self, **kwargs):
        self.pk = 1
        super().save(**kwargs)
        self.set_cache()

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        if cache.get(cls.__name__) is None:
            try:
                obj = cls.objects.get(pk=1)
            except cls.DoesNotExist:
                return cls.objects.none()
            obj.set_cache()
        return cache.get(cls.__name__)


class FernetEncryptedCharField(models.CharField):
    def get_prep_value(self, value):
        if value is None:
            return value

        # If it's already encrypted, leave it alone
        try:
            fernet.decrypt(value.encode())
            return value
        except InvalidToken:
            return fernet.encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return fernet.decrypt(value.encode()).decode()


class AppSettings(SingletonModel):

    class Meta:
        verbose_name = "App Settings"
        verbose_name_plural = "App Settings"

    sandbox_mode = models.BooleanField(default=False,
                                       help_text="Sandbox mode. Bypasses all Cloudflare and UpCloud functions")
    upcloud_api_username = FernetEncryptedCharField(max_length=255)
    upcloud_api_password = FernetEncryptedCharField(max_length=255)
    upcloud_api_url = models.CharField(max_length=255)
    init_script_url = models.URLField(max_length=255)

    cloudflare_api_token = FernetEncryptedCharField(max_length=255)
    cloudflare_turnstile_key = FernetEncryptedCharField(max_length=255)
    cloudflare_turnstile_secret = FernetEncryptedCharField(max_length=255)

    mailjet_api_key = FernetEncryptedCharField(max_length=255)
    mailjet_api_secret = FernetEncryptedCharField(max_length=255)


class PortfolioItem(TimeStampedModel):
    heading = models.CharField(max_length=255)
    subtitle = models.TextField(blank=True, null=True)
    text = models.TextField(blank=True, null=True)

    image = models.ImageField(blank=True, null=True,
                              help_text="Aspect ratio must be 2.4:1 (example: 960x400px)")

    url = models.URLField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return self.heading


class ExternalURL(TimeStampedModel):
    portfolio_item = models.ForeignKey(PortfolioItem, on_delete=models.CASCADE, related_name='external_urls')
    url = models.URLField()
    title = models.CharField(max_length=255)
    sort_order = models.IntegerField(default=0)
    visible = models.BooleanField(default=True)


class Testimonial(TimeStampedModel):
    portfolio_item = models.ForeignKey('PortfolioItem', on_delete=models.CASCADE, related_name='testimonials')
    by = models.CharField(max_length=255)
    text = models.TextField()
    visible = models.BooleanField(default=True)


class Request(TimeStampedModel):
    # a pre_save signal will prepare an email for the requester
    party_name = models.CharField(max_length=255)
    party_url = models.URLField(blank=True, null=True, help_text="URL to the party's official website")
    contact_email = models.EmailField(help_text="Contact email for the party organizer(s)")
    party_start = models.DateField()
    party_end = models.DateField()
    inception_date = models.DateField(help_text="Date when the instance should be online")
    extra_info = models.TextField(blank=True, null=True,
                                  help_text="Any extra information we might need. If the instance needs to be online " \
                                            "much in advance, a reason should be given.")
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
    activated_by = models.ForeignKey(get_user_model(), blank=True, null=True, on_delete=models.SET_NULL,
                                     related_name='activations')
    deactivated = models.DateTimeField(blank=True, null=True)
    deactivated_by = models.ForeignKey(get_user_model(), blank=True, null=True, on_delete=models.SET_NULL,
                                       related_name='deactivations')

    def __str__(self):
        return f"{self.party_name} ({self.party_start.year})"


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


class SSHKeys(TimeStampedModel):
    class Meta:
        verbose_name = "SSH Keys"
        verbose_name_plural = "SSH Keys"

    user = models.CharField(max_length=255)
    public_key = models.TextField()

    def __str__(self):
        return self.user


class Email(TimeStampedModel):
    # a pre_save signal will deliver the email and populate status fields
    recipients = models.JSONField()
    subject = models.CharField(max_length=255)
    text_content = models.TextField()
    html_content = models.TextField(blank=True, null=True)
    delivery_status_code = models.IntegerField(blank=True, null=True)
    delivery_status_json = models.JSONField(blank=True, null=True)
