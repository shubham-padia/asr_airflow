from rest_framework import generics
from .models import MetadataRegistry
from .serializers import MetadataRegistrySerializer


class ListMetadataRegistry(generics.ListAPIView):
    """
    Provides a get method handler.
    """
    queryset = MetadataRegistry.objects.all()
    serializer_class = MetadataRegistrySerializer
