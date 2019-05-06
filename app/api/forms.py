from django import forms

class UploadAudioForm(forms.Form):
    recording_id = forms.CharField(max_length=255)
    pipeline_id = forms.CharField(max_length=255)
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
