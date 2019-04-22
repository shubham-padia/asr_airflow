from rest_framework import generics
from .models import MetadataRegistry
from .serializers import MetadataRegistrySerializer

class ListMetadataRegistry(generics.ListCreateAPIView):
    """
    Create an entry in the metadata registry or get a list of all the entries.
    """

    queryset = MetadataRegistry.objects.all()
    serializer_class = MetadataRegistrySerializer
