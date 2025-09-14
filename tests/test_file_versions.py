import os
import shutil
from unittest.mock import MagicMock

from pytest import raises
from unittest import mock
from rest_framework.exceptions import ValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.test import APITestCase

from propylon_document_manager.file_versions.api.views import FileVersionRetrieveView, FileVersionViewSet, \
    get_directories
from propylon_document_manager.file_versions.models import FileVersion, User


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
    result = FileVersionViewSet.validate_file_url(file_url)
    assert result == file_url

def test_validate_file_url_with_leading_slash():
    """
    Tests validate_file_url with a valid file url
    starting with a leading slash
    """
    file_url = "/documents/report.pdf"
    result = FileVersionViewSet.validate_file_url(file_url)
    assert result == "documents/report.pdf"

def test_validate_file_url_empty():
    """Tests validate_file_url with an empty file url"""
    file_url = ""
    with raises(ValidationError):
        FileVersionViewSet.validate_file_url(file_url)

def test_validate_file_url_no_extension():
    """Tests validate_file_url with a file url without extension"""
    file_url = "documents/report"
    with raises(ValidationError):
        FileVersionViewSet.validate_file_url(file_url)

@mock.patch("propylon_document_manager.file_versions.api.views.os.getcwd")
def test_get_directories(mock_getcwd):
    """Tests get_directories for returning correct paths."""
    path_to_media = ['src', 'propylon_document_manager', 'media']
    mock_getcwd.return_value = "/path/to/app"

    file_url = "path/to/new_file.txt"

    media_path, new_file_name = get_directories(file_url)

    expected_media_path = os.path.join("/path/to/app", *path_to_media)
    expected_new_file_name = "new_file.txt"

    assert media_path == expected_media_path
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

        self.hash_1 = "09fe6143410320a2d4a0bdfd782af8438e869fc531c5b06eab67c035649f3d78"
        self.file_path_1 = os.path.join(self.test_dir, self.hash_1)
        os.makedirs(os.path.dirname(self.file_path_1), exist_ok=True)
        with open(self.file_path_1, 'w') as f:
            f.write("This is version 1.")

        self.file_version_1 = FileVersion.objects.create(
            user_id=self.user.id,
            file_url=self.file_url,
            version_number=self.version_number_1,
            file_hash=self.hash_1
        )

        self.hash_2 = "528836fe05ab87f6b062f9f58cb95429920dc27a8a1ccde2f00e11e100c6fb80"
        self.file_path_2 = os.path.join(self.test_dir, self.hash_2)
        os.makedirs(os.path.dirname(self.file_path_2), exist_ok=True)
        with open(self.file_path_2, 'w') as f:
            f.write("This is version 2.")

        self.file_version_2 = FileVersion.objects.create(
            user_id=self.user.id,
            file_url=self.file_url,
            version_number=self.version_number_2,
            file_hash=self.hash_2
        )

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)

    @mock.patch("propylon_document_manager.file_versions.api.views.PATH_TO_MEDIA", ["test_dir"])
    def test_retrieve_latest_version(self):
        """
        Tests that the latest file version is retrieved when no revision is specified.
        """
        response = FileVersionRetrieveView().get(self.request, self.file_url)

        assert response.status_code == status.HTTP_200_OK

        expected_content = bytes("This is version 2.", 'utf-8')
        response_content = b''.join(response.streaming_content)
        assert response_content == expected_content

    @mock.patch("propylon_document_manager.file_versions.api.views.PATH_TO_MEDIA", ["test_dir"])
    def test_retrieve_specific_version(self):
        """
        Tests that the latest file version is retrieved when a revision is specified.
        """
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

    @mock.patch("propylon_document_manager.file_versions.api.views.os.getcwd")
    def test_file_not_found_on_disk(self, mock_getcwd):
        """
        Tests that an Http404 is raised when the file version exists in the database but not on disk.
        """
        mock_getcwd.return_value = "wrong/path"

        self.file_version_1 = FileVersion.objects.create(
            user_id=self.user.id,
            file_url=self.file_url,
            version_number=self.version_number_1,
            file_hash=self.hash_1
        )

        with raises(Http404):
            FileVersionRetrieveView().get(self.request, self.file_url)


def test_no_file_provided(user):
    """
    Tests that a ValidationError is raised when no file is provided to create()
    """
    file_url = "test/file.txt"
    request = mock.MagicMock(user=user, data={"file_url": file_url})

    with raises(ValidationError) as exc_info:
        FileVersionViewSet().create(request)
    assert exc_info.value.detail['detail'] == 'No file provided'


@mock.patch("propylon_document_manager.file_versions.models.FileVersion.objects")
@mock.patch("propylon_document_manager.file_versions.api.views.sha256")
def test_same_file_hash_skips_saving(mock_sha256, mock_file_version_model, user):
    """
    Tests that no new files are saved if the hash is the same
    """
    file = MagicMock()
    file_hash = "09fe6143410320a2d4a0bdfd782af8438e869fc531c5b06eab67c035649f3d78"
    file_url = "test/file.txt"
    mock_sha256.return_value.hexdigest.return_value = file_hash

    latest_version_mock = MagicMock()
    latest_version_mock.file_url = file_url
    latest_version_mock.file_hash = file_hash
    latest_version_mock.version_number = 1

    mock_file_version_model.filter.return_value.order_by.return_value.first.return_value = latest_version_mock

    request = MagicMock(user=user, data={"file_url": file_url, "file": file})
    response = FileVersionViewSet().create(request)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["version_number"] == 1
    assert response.data["file_url"] == file_url
    assert mock_file_version_model.create.not_called()


@mock.patch("propylon_document_manager.file_versions.api.views.Path.mkdir")
@mock.patch("propylon_document_manager.file_versions.api.views.open", new_callable=mock.mock_open)
@mock.patch("propylon_document_manager.file_versions.api.views.get_directories", return_value=("media/path", "file.txt"))
@mock.patch("propylon_document_manager.file_versions.models.FileVersion.objects")
@mock.patch("propylon_document_manager.file_versions.api.views.sha256")
def test_new_file_saves_correctly(mock_sha256, mock_file_version_model, mock_get_dirs, mock_open_file, mock_mkdir, user):
    """
    Tests that files are created
    """
    file = MagicMock()
    file_hash = "09fe6143410320a2d4a0bdfd782af8438e869fc531c5b06eab67c035649f3d78"
    file_url = "test/file.txt"
    mock_sha256.return_value.hexdigest.return_value = file_hash

    # No latest version found
    mock_file_version_model.filter.return_value.order_by.return_value.first.return_value = None
    # No existing file with the same hash
    mock_file_version_model.filter.return_value.first.return_value = None

    mock_file_version_model.create.return_value = mock.Mock(
        file_url=file_url,
        version_number=0
    )

    request = MagicMock(user=user, data={"file_url": file_url, "file": file})
    response = FileVersionViewSet().create(request)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["version_number"] == 0
    assert mock_mkdir.called
    mock_open_file.assert_called_once_with(os.path.join("media/path", file_hash), "wb")
    mock_file_version_model.create.assert_called_once()


def test_partial_update_file_not_found(user):
    """
    Tests that an Http404 is raised when the file is not found in the database.
    """
    request = MagicMock(user=user, data={})

    with raises(Http404):
        FileVersionViewSet().partial_update(request, pk=1111)


@mock.patch("propylon_document_manager.file_versions.api.views.User.objects")
@mock.patch("propylon_document_manager.file_versions.api.views.FileVersion.objects")
def test_partial_update_read_permissions_updated(mock_file_version_objects, mock_user_objects, patch_file_version, user):
    """
    Tests that read permissions are being updated
    """
    mock_file_version = patch_file_version

    mock_user_objects.filter.return_value.all.return_value = [user]
    mock_file_version_objects.filter.return_value.first.return_value = mock_file_version

    data = {"read_permissions": ["user@example.com"]}

    request = MagicMock(data=data)
    response = FileVersionViewSet().partial_update(request, pk=1)

    mock_file_version.read_permissions.clear.assert_called_once()
    mock_file_version.read_permissions.add.assert_called_once_with(user)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == mock_file_version.id


@mock.patch("propylon_document_manager.file_versions.api.views.User.objects")
@mock.patch("propylon_document_manager.file_versions.api.views.FileVersion.objects")
def test_partial_update_write_permissions_updated(mock_file_version_objects, mock_user_objects, patch_file_version, user):
    """
    Tests that write permissions are being updated
    """
    mock_file_version = patch_file_version

    mock_user_objects.filter.return_value.all.return_value = [user]
    mock_file_version_objects.filter.return_value.first.return_value = mock_file_version

    data = {"write_permissions": ["user@example.com"]}

    request = MagicMock(data=data)
    response = FileVersionViewSet().partial_update(request, pk=1)

    mock_file_version.write_permissions.clear.assert_called_once()
    mock_file_version.write_permissions.add.assert_called_once_with(user)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == mock_file_version.id


@mock.patch("propylon_document_manager.file_versions.api.views.User.objects")
@mock.patch("propylon_document_manager.file_versions.api.views.FileVersion.objects")
def test_partial_update_both_permissions(mock_file_version_objects, mock_user_objects, patch_file_version, user):
    """
    Tests that both read and write permissions are being updated
    """
    mock_file_version = patch_file_version

    mock_file_version.read_permissions.all.return_value = []
    mock_file_version.write_permissions.all.return_value = []

    mock_user_objects.filter.return_value.all.return_value = [user]
    mock_file_version_objects.filter.return_value.first.return_value = mock_file_version

    data = {
        "read_permissions": ["user@example.com"],
        "write_permissions": ["user@example.com"]
    }
    request = MagicMock(data=data)
    response = FileVersionViewSet().partial_update(request, pk=1)

    mock_file_version.read_permissions.clear.assert_called_once()
    mock_file_version.write_permissions.clear.assert_called_once()
    mock_file_version.read_permissions.add.assert_called_once_with(user)
    mock_file_version.write_permissions.add.assert_called_once_with(user)
    assert response.status_code == status.HTTP_200_OK
