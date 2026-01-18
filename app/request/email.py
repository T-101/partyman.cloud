import re
import threading

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from request.models import Email, Request


def render_emails(request: Request, template_file: str) -> tuple[str, str]:
    html = render_to_string(template_file, {'request': request})
    text = re.sub(r"(.*)<style.*</style>(.*)", r"\1\2", html, count=0, flags=re.DOTALL)
    return html, strip_tags(text.strip())


def _generate_request_email(request: Request, subject, html, text, recipients: list = []):
    recipients = recipients if recipients else [request.contact_email]
    customer_mail = Email(recipients=recipients, subject=subject, text_content=text, html_content=html)
    threading.Thread(target=customer_mail.save, daemon=True).start()


def generate_request_received_admin_email(request):
    html, text = render_emails(request, template_file="request-received-admin.html")
    subject = f"New PartyMan request: {request.party_name} {request.party_start.year}"
    _generate_request_email(request, subject, html, text, settings.ADMINS)


def generate_request_received_email(request):
    html, text = render_emails(request, template_file="request-received.html")
    subject = f"Your PartyMan request: {request.party_name} {request.party_start.year}"
    _generate_request_email(request, subject, html, text)


def generate_request_activation_email(request):
    html, text = render_emails(request, template_file="request-activated.html")
    subject = f"Your PartyMan request: {request.party_name} {request.party_start.year}"
    _generate_request_email(request, subject, html, text)
