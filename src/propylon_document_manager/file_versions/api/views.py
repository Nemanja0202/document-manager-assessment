from django.http import Http404

from rest_framework import status
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from ..models import FileVersion
from .serializers import FileVersionSerializer

class FileVersionViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = FileVersionSerializer
    queryset = FileVersion.objects.all()
    lookup_field = "file_name"

    def create(self, validated_data):
        file_name = validated_data.data.get("file_name")
        user_id = validated_data.user.id

        version_number = 0
        if file := FileVersion.objects.filter(file_name=file_name, user_id=user_id).order_by("-version_number").first():
            version_number = file.version_number + 1

        file_version = FileVersion.objects.create(
            file_name=file_name,
            version_number=version_number,
            user_id=user_id
        )

        serilizer = self.serializer_class(file_version)
        return Response(serilizer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *ags, **kwargs):
        file_name = self.kwargs.get("file_name")
        user_id = request.user.id

        if version_number := request.query_params.get("version_number"):
            file_version = FileVersion.objects.filter(
                file_name=file_name,
                user_id=user_id,
                version_number=version_number
            ).first()
        else:
            file_version = FileVersion.objects.filter(
                file_name=file_name,
                user_id=user_id
            ).order_by("-version_number").first()

        if not file_version:
            raise Http404("File not found")

        serilizer = self.serializer_class(file_version)
        return Response(serilizer.data)
