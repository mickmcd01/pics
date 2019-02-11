from django import forms

class SearchPicturesForm(forms.Form):
    search_text = forms.CharField(label='Title', max_length=100, required=False)
    start_date = forms.DateField(label='Earliest date', required=False)
    end_date = forms.DateField(label='Latest date', required=False)
    