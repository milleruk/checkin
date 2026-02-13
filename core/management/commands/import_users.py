import json
from django.core.management.base import BaseCommand
from core.models import User

class Command(BaseCommand):
    help = 'Import users from users.json (converted for custom user model)'

    def handle(self, *args, **options):
        with open('users.json') as f:
            data = json.load(f)
        for obj in data:
            fields = obj['fields']
            email = fields.get('email') or fields.get('username')
            if not email:
                self.stdout.write(self.style.ERROR('No email/username for user'))
                continue
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'is_active': fields.get('is_active', True),
                    'is_staff': fields.get('is_staff', False),
                    'is_superuser': fields.get('is_superuser', False),
                    'password': fields.get('password', ''),
                    'first_name': fields.get('first_name', ''),
                    'last_name': fields.get('last_name', ''),
                    'last_login': fields.get('last_login'),
                    'date_joined': fields.get('date_joined'),
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created user: {email}'))
            else:
                self.stdout.write(f'User already exists: {email}')
