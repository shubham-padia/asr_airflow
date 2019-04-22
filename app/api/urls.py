from django.urls import path
from .views import ListMetadataRegistry

urlpatterns = [
    path('metadata-registry/', ListMetadataRegistry.as_view(), name="metadata-registry")
]