import threading

from mailjet_rest import Client

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.conf import settings

from request.models import Request, Email
from request.email import render_emails


# This file is imported in apps.py

@receiver(pre_save, sender=Request)
def prepare_request_received_emails(sender, instance, *args, **kwargs):
    if instance.pk:
        return

    html, text = render_emails(instance, "request-received.html")
    subject = f"Your PartyMan instance {instance.party_name}"
    customer_mail = Email(recipients=[instance.contact_email], subject=subject, text_content=text, html_content=html)

    subject = f"New PartyMan request: {instance.party_name}"
    text = f"{instance.party_name} requested by {instance.contact_email}\n\n" \
           f"Requested inception {instance.party_start}"
    admin_email = Email(recipients=settings.ADMINS, subject=subject, text_content=text)

    for item in [customer_mail, admin_email]:
        threading.Thread(
            target=item.save,
            daemon=True
        ).start()


@receiver(pre_save, sender=Email)
def send_email(sender, instance, **kwargs):
    mailjet = Client(auth=(settings.MAILJET_API_KEY, settings.MAILJET_API_SECRET), version='v3.1')
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
