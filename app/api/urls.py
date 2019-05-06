from django.urls import path
from .views import ListMetadataRegistry, UploadAudio

urlpatterns = [
    path('metadata-registry', ListMetadataRegistry.as_view(), name="metadata-registry"),
    path('upload-audio', UploadAudio.as_view(), name="upload-audio")
]