from django.conf import settings
from django.urls import include, path, re_path

from rest_framework.authtoken.views import obtain_auth_token

from propylon_document_manager.file_versions.api.views import FileVersionUploadView, FileVersionRetrieveView

# API URLS
urlpatterns = [
    # API base url
    path("api/", include("propylon_document_manager.site.api_router")),
    # DRF auth token
    path("api-auth/", include("rest_framework.urls")),
    path("auth-token/", obtain_auth_token),
    path('files/upload/', FileVersionUploadView.as_view()),
]

if settings.DEBUG:
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
