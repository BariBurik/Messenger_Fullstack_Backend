from django.core.management.base import BaseCommand
from strawberry.printer import print_schema
from messenger.strawberry import schema


class Command(BaseCommand):
    help = 'Export the Strawberry schema to SDL'

    def handle(self, *args, **options):
        sdl = print_schema(schema)
        with open('strawberry_schema.graphql', 'w') as f:
            f.write(sdl)
        self.stdout.write(self.style.SUCCESS('Successfully exported Strawberry schema'))
