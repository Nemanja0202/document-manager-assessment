import os
from hashlib import sha256
from pathlib import Path

from django.http import FileResponse, Http404
from rest_framework import generics
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from ..models import FileVersion, User
from .serializers import FileVersionSerializer, RegisterSerializer


PATH_TO_MEDIA = ['src', 'propylon_document_manager', 'media']


def get_directories(file_url):
    new_file_directories = file_url.split("/")
    new_file_name = new_file_directories.pop()

    media_path = os.path.join(os.getcwd(), *PATH_TO_MEDIA)

    return media_path, new_file_name


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
            {"file_url": file_version.file_url, "version_number": file_version.version_number},
            status=status.HTTP_201_CREATED
        )


class FileVersionRetrieveView(APIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, file_url):
        user_id = request.user.id
        version_number = request.query_params.get("revision")

        if version_number:
            file_version = FileVersion.objects.filter(
                file_url=file_url,
                user_id=user_id,
                version_number=version_number
            ).first()
        else:
            file_version = FileVersion.objects.filter(
                file_url=file_url,
                user_id=user_id
            ).order_by("-version_number").first()

        if not file_version:
            raise Http404("File not found")

        download_path = os.path.join(os.getcwd(), *PATH_TO_MEDIA, file_version.file_hash)

        if not os.path.exists(download_path):
            raise Http404("File not found")

        with open(download_path, "rb") as f:
            return FileResponse(f.read().decode(), content_type='application/octet-stream')


class FileVersionViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    authentication_classes = []
    permission_classes = []
    serializer_class = FileVersionSerializer
    queryset = FileVersion.objects.all()
    lookup_field = "id"


class RegisterView(generics.CreateAPIView):
    authentication_classes = []
    permission_classes = []
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
