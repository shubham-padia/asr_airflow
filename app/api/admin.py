from django.contrib import admin
from .models import MetadataRegistry

class MetadataRegistryAdmin(admin.ModelAdmin):
    list_display = ['version', 'created_at', 'status']
    list_filter = ('version', 'created_at', 'status') 

admin.site.register(MetadataRegistry, MetadataRegistryAdmin)