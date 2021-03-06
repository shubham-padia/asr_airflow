import datetime

from django.db import models
from django.contrib.postgres.fields import JSONField

class MetadataRegistry(models.Model):

    class Meta:
        db_table = 'metadata_registry'
    
    recording_id = models.CharField(max_length=256, null=False, blank=False)
    pipeline_id = models.CharField(max_length=256, null=False, blank=False)
    status = models.BooleanField(default=False)
    version = models.CharField(max_length=256, null=False, blank=False)
    # Make sure you aren't using default=datetime.datetime.utcnow(); you want
    # to pass the utcnow function, not the result of evaluating it at module
    # load.
    created_at = models.DateTimeField(default=datetime.datetime.utcnow)

    pipeline = JSONField()
