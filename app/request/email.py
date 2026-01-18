import re
import threading

from django.template.loader import render_to_string
from django.utils.html import strip_tags
from request.models import Email, Request


def render_emails(request: Request, template_file: str) -> tuple[str, str]:
    html = render_to_string(template_file, {'request': request})
    text = re.sub(r"(.*)<style.*</style>(.*)", r"\1\2", html, count=0, flags=re.DOTALL)
    return html, strip_tags(text.strip())


def _generate_request_email(request: Request, html, text, recipients: list):
    recipients = recipients if recipients else [request.contact_email]
    subject = f"Your PartyMan instance {request.party_name} {request.party_start.year}"
    customer_mail = Email(recipients=recipients, subject=subject, text_content=text, html_content=html)

    threading.Thread(target=customer_mail.save, daemon=True).start()


def generate_request_received_email(request, recipients: list = []):
    html, text = render_emails(request, template_file="request-received.html")
    _generate_request_email(request, html, text, recipients)


def generate_request_activation_email(request, recipients: list = []):
    html, text = render_emails(request, template_file="request-activated.html")
    _generate_request_email(request, html, text, recipients)
