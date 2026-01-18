import re

from django.template.loader import render_to_string
from django.utils.html import strip_tags


def render_emails(request, template_file: str) -> tuple[str, str]:
    html = render_to_string(template_file, {'request': request})
    text = re.sub(r"(.*)<style.*</style>(.*)", r"\1\2", html, count=0, flags=re.DOTALL)
    return html, strip_tags(text.strip())
