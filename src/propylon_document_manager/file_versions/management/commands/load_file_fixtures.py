from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from propylon_document_manager.file_versions.models import FileVersion, User

file_versions = [
    'bill_document',
    'amendment_document',
    'act_document',
    'statute_document',
]

class Command(BaseCommand):
    help = "Load admin user and basic file version fixtures"

    def handle(self, *args, **options):
        User.objects.create(
            name='admin',
            email='admin@pdm.test',
            password='admin',
            is_superuser=True,
            is_staff=True,
            is_active=True,
            date_joined=datetime.now(timezone.utc),
        )

        self.stdout.write(
            self.style.SUCCESS('Successfully created admin user')
        )

        for file_name in file_versions:
            FileVersion.objects.create(
                file_name=file_name,
                version_number=1,
                user_id=1
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully created %s file versions' % len(file_versions))
        )
