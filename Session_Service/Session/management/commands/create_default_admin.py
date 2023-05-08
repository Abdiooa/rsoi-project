from django.core.management.base import BaseCommand
from Session.models import Users

class Command(BaseCommand):
    help = 'Creates the default admin user.'

    def handle(self, *args, **options):
        if Users.objects.filter(role='admin').exists():
            self.stdout.write(self.style.WARNING('An admin user already exists. Skipping default admin creation.'))
            return
        user =  Users(
            username = "Admin",
            name = "Abdi",
            role = 'admin',
            last_name = "ousleyeh",
            email = 'admin@example.com'
        )
        user.set_password('Abdi2000*')
        user.save()
        self.stdout.write(self.style.SUCCESS('Default admin user created successfully.'))
