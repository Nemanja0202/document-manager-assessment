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
        default_user = User.objects.create_user(
            username='default',
            email='default@pdm.test',
            password='default',
            is_superuser=False,
            is_staff=False,
            is_active=True,
            date_joined=datetime.now(timezone.utc),
        )

        self.stdout.write(
            self.style.SUCCESS('Successfully created admin user')
        )

        for file_name in file_versions:
            FileVersion.objects.create(
                file_name=file_name,
                version_number=0,
                user_id=default_user.id,
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully created %s file versions' % len(file_versions))
        )
