from unittest import mock

import pytest

from propylon_document_manager.file_versions.models import User
from .factories import UserFactory

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass

@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()

@pytest.fixture
def patch_file_version():
    mock_file_version = mock.Mock()
    mock_file_version.id = 1
    mock_file_version.file_url = "path/file.txt"
    mock_file_version.version_number = 0

    mock_file_version.read_permissions.all.return_value = []
    mock_file_version.write_permissions.all.return_value = []

    return mock_file_version
