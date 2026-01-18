# request/management/commands/cleanup_dramatiq.py
from django.core.management.base import BaseCommand
from django_dramatiq.tasks import delete_old_tasks


class Command(BaseCommand):
    help = "Cleanup old django-dramatiq task records"

    def handle(self, *args, **options):
        delete_old_tasks.send(max_task_age=60 * 60 * 24)
