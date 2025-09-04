import os
import shutil
from hashlib import sha256
from pathlib import Path

from rest_framework import status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from ..models import FileVersion
from .serializers import FileVersionSerializer


PATH_TO_MEDIA = ['src', 'propylon_document_manager', 'media']


class FileVersionUploadView(APIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @staticmethod
    def validate_file_url(file_url):
        if not file_url:
            raise ValidationError({"detail": "File URL cannot be empty"})

        if "." not in file_url:
            raise ValidationError({"detail": "URL with file extension required"})

        if file_url[0] == '/':
            file_url = file_url[1:]

        return file_url

    @staticmethod
    def get_directories(file_url, user_id, version_number):
        new_file_directories = file_url.split("/")
        new_file_name = new_file_directories.pop()

        media_path = os.path.join(os.getcwd(), *PATH_TO_MEDIA)
        new_file_path = os.path.join(media_path, str(user_id), *new_file_directories, str(version_number))

        return media_path, new_file_path, new_file_name

    def post(self, request):
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

        media_path, new_file_path, new_file_name = self.get_directories(file_url, user_id, version_number)
        Path(new_file_path).mkdir(parents=True, exist_ok=True)

        file_version = FileVersion.objects.create(
            file_name=new_file_name,
            version_number=version_number,
            file_url=file_url,
            file_hash=file_hash,
            file=file,
            user_id=user_id
        )

        temp_file = os.path.join(media_path, file.name)
        new_file = os.path.join(new_file_path, new_file_name)
        try:
            shutil.move(temp_file, new_file)
        except (FileNotFoundError, Exception) as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            file_version.delete()
            raise e

        return Response(
            {"file_url": file_version.file_url, "version_number": file_version.version_number},
            status=status.HTTP_201_CREATED
        )


class FileVersionViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    authentication_classes = []
    permission_classes = []
    serializer_class = FileVersionSerializer
    queryset = FileVersion.objects.all()
    lookup_field = "file_name"
