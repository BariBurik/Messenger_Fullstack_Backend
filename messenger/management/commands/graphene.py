from django.core.management.base import BaseCommand
from graphql import print_schema
from messenger.graphene import graphene_schema


class Command(BaseCommand):
    help = 'Export the Graphene schema to SDL'

    def handle(self, *args, **options):
        sdl = print_schema(graphene_schema.graphql_schema)
        with open('graphene_schema.graphql', 'w') as f:
            f.write(sdl)
        self.stdout.write(self.style.SUCCESS('Successfully exported Graphene schema'))