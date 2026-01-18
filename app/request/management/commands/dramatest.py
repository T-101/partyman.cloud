from django.core.management.base import BaseCommand
from request.tasks import do_something

class Command(BaseCommand):
    help = "Testing dramatiq send queue"

    def handle(self, *args, **options):
        print("ASDF! ASDF! ASDF!")
        do_something.send()
