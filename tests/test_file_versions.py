import os
from pytest import raises
from unittest import mock

from rest_framework.exceptions import ValidationError

from propylon_document_manager.file_versions.api.views import FileVersionUploadView
from propylon_document_manager.file_versions.models import FileVersion

PATH_TO_MEDIA = ['src', 'propylon_document_manager', 'media']

def test_file_versions(user):
    file_name = "new_file"
    file_version = 1
    FileVersion.objects.create(
        file_name=file_name,
        version_number=file_version,
        user_id=user.id
    )
    files = FileVersion.objects.all()
    assert files.count() == 1
    assert files[0].file_name == file_name
    assert files[0].version_number == file_version
    assert files[0].user_id == user.id

def test_validate_file_url_valid():
    """Tests validate_file_url with a valid file url"""
    file_url = "documents/reviews/review.pdf"
    result = FileVersionUploadView.validate_file_url(file_url)
    assert result == file_url

def test_validate_file_url_with_leading_slash():
    """
    Tests validate_file_url with a valid file url
    starting with a leading slash
    """
    file_url = "/documents/report.pdf"
    result = FileVersionUploadView.validate_file_url(file_url)
    assert result == "documents/report.pdf"

def test_validate_file_url_empty():
    """Tests validate_file_url with an empty file url"""
    file_url = ""
    with raises(ValidationError):
        FileVersionUploadView.validate_file_url(file_url)

def test_validate_file_url_no_extension():
    """Tests validate_file_url with a file url without extension"""
    file_url = "documents/report"
    with raises(ValidationError):
        FileVersionUploadView.validate_file_url(file_url)

@mock.patch('propylon_document_manager.file_versions.api.views.os.getcwd',
            return_value="/path/to/app")
def test_get_directories(mock_getcwd):
    """Tests get_directories for returning correct paths."""
    file_url = "path/to/new_file.txt"
    user_id = 1
    version_number = 1

    media_path, new_file_path, new_file_name = FileVersionUploadView.get_directories(file_url, user_id, version_number)

    expected_media_path = os.path.join("/path/to/app", *PATH_TO_MEDIA)
    expected_new_file_path = os.path.join(expected_media_path, str(user_id), "path", "to", str(version_number))
    expected_new_file_name = "new_file.txt"

    assert media_path == expected_media_path
    assert new_file_path == expected_new_file_path
    assert new_file_name == expected_new_file_name
