from rest_framework import serializers
from .models import MetadataRegistry


class MetadataRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MetadataRegistry
        fields = ("recording_id", "pipeline_id", "pipeline", "status", "version", "created_at")
        read_only_fields = ('created_at',)
        extra_kwargs = {
            "recording_id": {"required": True},
            "pipeline_id": {"required": True},
            "pipeline": {"required": True},
            "version": {"required": True},
            "created_at": {"required": True}
        }

    def create(self, validated_data):
        return MetadataRegistry.objects.create(**validated_data)
