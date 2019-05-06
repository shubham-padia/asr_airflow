import os
import errno

from rest_framework import generics
from pathlib import Path
from django.http import JsonResponse
from django.views.generic.edit import FormView
from django.conf import settings

from .models import MetadataRegistry
from .serializers import MetadataRegistrySerializer
from .forms import UploadAudioForm

def create_dir_if_not_exists(directory):
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

class ListMetadataRegistry(generics.ListCreateAPIView):
    """
    Create an entry in the metadata registry or get a list of all the entries.
    """

    queryset = MetadataRegistry.objects.all()
    serializer_class = MetadataRegistrySerializer


class UploadAudio(FormView):
    form_class = UploadAudioForm

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('file')
        if form.is_valid():
            data = form.cleaned_data
            recording_id = data['recording_id']
            pipeline_id = data['pipeline_id']
            for f in files:
                directory = "%s/%s/%s" % (settings.MEDIA_ROOT, recording_id, pipeline_id)
                create_dir_if_not_exists(directory)
                with open(Path("%s/%s" % (directory, f.name)).resolve(), 'wb+') as destination:
                    for chunk in f.chunks():
                        destination.write(chunk)

            return JsonResponse({'form': True})
        else:
            print(form.errors)
            return JsonResponse({'form': False})
