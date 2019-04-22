from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status
from .models import MetadataRegistry
from .serializers import MetadataRegistrySerializer

class MetadataRegistryBaseViewTest(APITestCase):
    client = APIClient()

    @staticmethod
    def create_entry(pipeline={}, version="", status=False):
        if pipeline != {} and version != "":
            MetadataRegistry.objects.create(pipeline=pipeline, version=version, status=status)

    def setUp(self):
        # add test data
        self.create_entry(pipeline={"test": "json"}, version="0.0.1")
        self.create_entry(pipeline={"lorem": "ipsum"}, version="0.0.5")

class GetAllMetadataRegistryTest(MetadataRegistryBaseViewTest):

    def test_get_all_metadata_registry(self):
        """
        This test ensures that all metadata entries added in the setUp method
        exist when we make a GET request to the metadata-registry/ endpoint
        """
        # hit the API endpoint
        response = self.client.get(
            reverse("metadata-registry", kwargs={"version": "v1"})
        )
        # fetch the data from db
        expected = MetadataRegistry.objects.all()
        serialized = MetadataRegistrySerializer(expected, many=True)
        self.assertEqual(response.data, serialized.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
