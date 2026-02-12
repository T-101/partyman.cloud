from mailjet_rest import Client

from django.db.models.signals import pre_save
from django.dispatch import receiver

from request.models import Request, Email, AppSettings
from request.email import generate_request_received_admin_email, generate_request_received_email


# This file is imported in apps.py

@receiver(pre_save, sender=Request)
def prepare_request_received_emails(sender, instance, *args, **kwargs):
    if instance.pk:
        return

    generate_request_received_admin_email(instance)
    generate_request_received_email(instance)


@receiver(pre_save, sender=Email)
def send_email(sender, instance, **kwargs):
    settings = AppSettings.load()
    mailjet = Client(auth=(settings.mailjet_api_key, settings.mailjet_api_secret), version='v3.1')
    if instance.pk:
        return

    data = {
        'Messages': [
            {
                "From": {
                    "Email": "partyman@partyman.cloud",
                    "Name": "PartyMan admins"
                },
                "To": [{"Email": x, "Name": x} for x in instance.recipients],
                "Subject": instance.subject,
                "TextPart": instance.text_content,
                "HTMLPart": instance.html_content,
                "TrackOpens": "disabled"
            }
        ]
    }

    res = mailjet.send.create(data=data)
    instance.delivery_status_code = res.status_code
    instance.delivery_status_json = res.json()
    instance.hold_delivery = False
