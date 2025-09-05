import os
from pytest import raises
from unittest import mock, TestCase

from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient

from propylon_document_manager.file_versions.api.views import FileVersionUploadView, get_directories, \
    FileVersionRetrieveView
from propylon_document_manager.file_versions.models import FileVersion, User

import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock

from django.http import Http404, FileResponse
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


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

@mock.patch("propylon_document_manager.file_versions.api.views.os.getcwd",
            return_value="/path/to/app")
def test_get_directories(mock_getcwd):
    """Tests get_directories for returning correct paths."""
    file_url = "path/to/new_file.txt"
    user_id = 1
    version_number = 1

    media_path, new_file_path, new_file_name = get_directories(file_url, user_id, version_number)

    expected_media_path = os.path.join("/path/to/app", *PATH_TO_MEDIA)
    expected_new_file_path = os.path.join(expected_media_path, str(user_id), "path", "to", str(version_number))
    expected_new_file_name = "new_file.txt"

    assert media_path == expected_media_path
    assert new_file_path == expected_new_file_path
    assert new_file_name == expected_new_file_name

class FileVersionRetrieveViewTests(APITestCase):
    def setUp(self):
        self.file_url = "test/file.txt"
        self.version_number_1 = 1
        self.version_number_2 = 2

        # Create a mock User objects for testing
        self.user = User.objects.create(
            name="testuser",
            password="testuser",
        )

        self.request = mock.MagicMock(user=self.user, query_params={})

        # Create mock files and FileVersion objects for testing
        self.test_dir = os.path.join(os.getcwd(), "test_dir")

        self.file_dir_1 = os.path.join(self.test_dir, f"{self.user.id}", "test", f"{self.version_number_1}")
        self.file_path_1 = os.path.join(self.file_dir_1, "file.txt")
        os.makedirs(os.path.dirname(self.file_path_1), exist_ok=True)
        with open(self.file_path_1, 'w') as f:
            f.write("This is version 1.")

        self.file_version_1 = FileVersion.objects.create(
            user_id=self.user.id,
            file_url=self.file_url,
            version_number=self.version_number_1
        )

        self.file_dir_2 = os.path.join(self.test_dir, f"{self.user.id}", "test", f"{self.version_number_2}")
        self.file_path_2 = os.path.join(self.file_dir_2, "file.txt")
        os.makedirs(os.path.dirname(self.file_path_2), exist_ok=True)
        with open(self.file_path_2, 'w') as f:
            f.write("This is version 2.")

        self.file_version_2 = FileVersion.objects.create(
            user_id=self.user.id,
            file_url=self.file_url,
            version_number=self.version_number_2
        )

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)

    @mock.patch("propylon_document_manager.file_versions.api.views.get_directories")
    def test_retrieve_latest_version(self, mock_get_directories):
        """
        Tests that the latest file version is retrieved when no revision is specified.
        """
        mock_get_directories.return_value = ("_", self.file_dir_2, "file.txt")

        response = FileVersionRetrieveView().get(self.request, self.file_url)

        assert response.status_code == status.HTTP_200_OK

        expected_content = bytes("This is version 2.", 'utf-8')
        response_content = b''.join(response.streaming_content)
        assert response_content == expected_content

    @mock.patch("propylon_document_manager.file_versions.api.views.get_directories")
    def test_retrieve_specific_version(self, mock_get_directories):
        """
        Tests that the latest file version is retrieved when a revision is specified.
        """
        mock_get_directories.return_value = ("_", self.file_dir_1, "file.txt")
        request = self.request
        request.query_params = {"revision": 1}

        response = FileVersionRetrieveView().get(request, self.file_url)

        assert response.status_code == status.HTTP_200_OK

        expected_content = bytes("This is version 1.", 'utf-8')
        response_content = b''.join(response.streaming_content)
        assert response_content == expected_content

    def test_file_version_not_found(self):
        """
        Tests that an Http404 is raised when the file is not found in the database.
        """
        request = self.request
        request.user.id = 2

        with raises(Http404):
            FileVersionRetrieveView().get(request, self.file_url)

    @mock.patch("propylon_document_manager.file_versions.api.views.get_directories")
    def test_file_not_found_on_disk(self, mock_get_directories):
        """
        Tests that an Http404 is raised when the file version exists in the database but not on disk.
        """
        mock_get_directories.return_value = ("_", self.file_dir_2, "file.tx")
        with raises(Http404):
            FileVersionRetrieveView().get(self.request, self.file_url)


class FileTests(APITestCase):

    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.file_url = 'test/file.pdf'
        self.version_number_1 = 1
        self.version_number_2 = 2

        # Create a mock User objects for testing
        self.user = User.objects.create(
            name="testuser",
            password="testuser",
        )

        # Create a mock file and FileVersion objects for testing
        self.file_path_1 = os.path.join(self.test_dir, f'testuser/{self.version_number_1}/file.pdf')
        os.makedirs(os.path.dirname(self.file_path_1), exist_ok=True)
        with open(self.file_path_1, 'w') as f:
            f.write("This is version 1.")

        self.file_version_1 = FileVersion.objects.create(
            user_id=self.user.id,
            file_url=self.file_url,
            version_number=self.version_number_1
        )

        self.file_path_2 = os.path.join(self.test_dir, f'testuser/{self.version_number_2}/file.pdf')
        os.makedirs(os.path.dirname(self.file_path_2), exist_ok=True)
        with open(self.file_path_2, 'w') as f:
            f.write("This is version 2.")

        self.file_version_2 = FileVersion.objects.create(
            user_id=self.user.id,
            file_url=self.file_url,
            version_number=self.version_number_2
        )

        # Mock the `get_directories` function to use the temporary directory
        self.mock_get_directories = patch(
            'propylon_document_manager.file_versions.api.views.get_directories',
            return_value=('mock_dir', self.test_dir + f'/{self.user.id}/{self.version_number_1}', 'file.pdf')
        ).start()

        self.view = FileVersionRetrieveView.as_view()
        self.url = f"/files/{self.file_url}"
        # self.url = reverse('retrieve-file-version', kwargs={'file_url': self.file_url})

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
        self.mock_get_directories.stop()


    #

    #
    # def test_unauthenticated_request(self):
    #     """
    #     Tests that an unauthenticated request is denied with a 401 status code.
    #     """
    #     self.client.logout()
    #     response = self.client.get(self.url)
    #
    #     assert response.status_code == status.HTTP_401_UNAUTHORIZED
