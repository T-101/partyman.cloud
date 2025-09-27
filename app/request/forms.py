from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Row, Div, ButtonHolder, Submit
from django import forms
from django.forms import ModelForm
from .models import Request, CloudflareZone


class RequestForm(ModelForm):
    class Meta:
        model = Request
        fields = ['party_name', 'party_url', 'contact_email', 'party_start', 'party_end', 'domain', 'cloudflare_zone']

    cloudflare_zone = forms.ModelChoiceField(empty_label=None, queryset=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Div('party_name', css_class='form-group col-md-6 mb-0'),
                Div('party_url', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Div('contact_email', css_class='form-group col-md-6 mb-0'),

                css_class='form-row'
            ),
            Row(
                Div('party_start', css_class='form-group col-md-6 mb-0'),
                Div('party_end', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Div('domain', css_class='form-group col-md-6 mb-0'),
                Div('cloudflare_zone', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            ButtonHolder(
                Submit('submit', 'Submit'),
            )
        )

        self.fields['cloudflare_zone'].queryset = CloudflareZone.objects.filter(public=True)
        self.fields['cloudflare_zone'].label = "Partyman host"
