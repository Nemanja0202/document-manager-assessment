import os
from hashlib import sha256
from pathlib import Path

from django.db.models import Q
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from ..models import FileVersion, User
from .serializers import FileVersionSerializer


PATH_TO_MEDIA = ['src', 'propylon_document_manager', 'media']


def get_directories(file_url):
    new_file_directories = file_url.split("/")
    new_file_name = new_file_directories.pop()

    media_path = os.path.join(os.getcwd(), *PATH_TO_MEDIA)

    return media_path, new_file_name


class FileVersionRetrieveView(APIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, file_url):
        user_id = request.user.id
        version_number = request.query_params.get("revision")

        if version_number:
            base_query = FileVersion.objects.filter(
                file_url=file_url,
                version_number=version_number
            )
        else:
            base_query = FileVersion.objects.filter(file_url=file_url).order_by("-version_number")

        # Currently two or more users can upload files with the same url and share the files between them
        # This could maybe be fixed with an optional query param like user_id or is_uploader.

        # Searching for user's files first
        file_version = base_query.filter(user_id=user_id).first()
        if not file_version:
            # If no files are found, searching for files where user has permission
            file_version = base_query.filter(
                Q(read_permissions=user_id) |
                Q(write_permissions=user_id)
            ).first()

        if not file_version:
            raise Http404("File not found")

        download_path = os.path.join(os.getcwd(), *PATH_TO_MEDIA, file_version.file_hash)

        if not os.path.exists(download_path):
            raise Http404("File not found")

        with open(download_path, "rb") as f:
            return FileResponse(f.read().decode(), content_type='application/octet-stream')


class FileVersionViewSet(GenericViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = FileVersionSerializer
    queryset = FileVersion.objects.all()

    @staticmethod
    def validate_file_url(file_url):
        if not file_url:
            raise ValidationError({"detail": "File URL cannot be empty"})

        if "." not in file_url:
            raise ValidationError({"detail": "URL with file extension required"})

        if file_url[0] == '/':
            file_url = file_url[1:]

        return file_url

    def create(self, request):
        user_id = request.user.id

        file = request.data.get("file")
        if not file:
            raise ValidationError({"detail": "No file provided"})

        file_url = self.validate_file_url(request.data.get("file_url"))

        file_hash = sha256(file.read()).hexdigest()
        file.seek(0)

        latest_version = FileVersion.objects.filter(file_url=file_url, user_id=user_id).order_by(
            "-version_number").first()
        if latest_version and latest_version.file_hash == file_hash:
            # Same as latest version, skipping
            return Response(
                {"file_url": file_url, "version_number": latest_version.version_number},
                status=status.HTTP_201_CREATED
            )

        version_number = latest_version.version_number + 1 if latest_version else 0
        media_path, file_name = get_directories(file_url=file_url)

        existing_file = FileVersion.objects.filter(file_hash=file_hash).first()
        if not existing_file:
            Path(media_path).mkdir(parents=True, exist_ok=True)
            with open(os.path.join(media_path, file_hash), "wb") as f:
                f.write(file.read())

        file_version = FileVersion.objects.create(
            file_name=file_name,
            version_number=version_number,
            file_url=file_url,
            file_hash=file_hash,
            user_id=user_id
        )

        return Response(
            {
                "id": file_version.id,
                "file_url": file_version.file_url,
                "version_number": file_version.version_number
            },
            status=status.HTTP_201_CREATED
        )

    def partial_update(self, request, pk=None):
        file_version = FileVersion.objects.get(pk=pk)
        if not file_version:
            raise Http404("File not found")

        read_permissions_request = request.data.get("read_permissions")
        write_permissions_request = request.data.get("write_permissions")

        # TODO Maybe add option to change file_url
        # Check if there's a file with the same file_url, but not that file itself - it should be possible to overwrite
        # url with the same name
        #   If not, update new file_url
        #   If yes but same file, update (basically skip)
        #   If yes but different file, raise error so we don't update
        # If updating file_url of a file with multiple revisions, all revisions should be updated

        if isinstance(read_permissions_request, list):
            # Deleting users from the permissions list
            file_version.read_permissions.clear()

            users = User.objects.filter(email__in=read_permissions_request).all()
            # Adding requested users to the permissions list
            for user in users:
                if user.id not in file_version.read_permissions.all():
                    file_version.read_permissions.add(user)

        if isinstance(write_permissions_request, list):
            # Deleting users from the permissions list
            file_version.write_permissions.clear()

            users = User.objects.filter(email__in=write_permissions_request).all()
            # Adding requested users to the permissions list
            for user in users:
                if user.id not in file_version.write_permissions.all():
                    file_version.write_permissions.add(user)

        return Response(
            {
                "id": file_version.id,
                "file_url": file_version.file_url,
                "version_number": file_version.version_number
            },
            status=status.HTTP_200_OK
        )
