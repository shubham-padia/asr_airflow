from django.contrib import admin
from .models import MetadataRegistry

class MetadataRegistryAdmin(admin.ModelAdmin):
    list_display = ['recording_id', 'pipeline_id', 'version', 'created_at', 'status']
    list_filter = ('recording_id', 'pipeline_id', 'version', 'created_at', 'status') 

admin.site.register(MetadataRegistry, MetadataRegistryAdmin)