from django import forms

class UploadAudioForm(forms.Form):
    recording_id = forms.CharField(max_length=255, error_messages={'required': 'Please enter the recording id'})
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), error_messages={'required': 'Please upload atleast one file.'})
