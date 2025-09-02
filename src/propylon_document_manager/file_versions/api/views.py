from django.shortcuts import render

from rest_framework import status
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from ..models import FileVersion
from .serializers import FileVersionSerializer

class FileVersionViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    authentication_classes = []
    permission_classes = []
    serializer_class = FileVersionSerializer
    queryset = FileVersion.objects.all()
    lookup_field = "id"

    def create(self, validated_data):
        file_name = validated_data.data.get("file_name")

        version_number = 0
        if file := FileVersion.objects.filter(file_name=file_name).order_by("-version_number").first():
            version_number = file.version_number + 1

        file_version = FileVersion.objects.create(file_name=file_name, version_number=version_number)

        serilizer = self.serializer_class(file_version)
        return Response(serilizer.data, status=status.HTTP_201_CREATED)
