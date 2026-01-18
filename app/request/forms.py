from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Row, Div, ButtonHolder, Submit
from django_cf_turnstile.fields import TurnstileCaptchaField
from django import forms
from django.forms import ModelForm
from .models import Request, CloudflareZone


class RequestForm(ModelForm):
    class Meta:
        model = Request
        fields = ['party_name', 'party_url', 'contact_email', 'party_start', 'party_end', 'domain', 'cloudflare_zone',
                  'inception_date', 'extra_info', 'captcha']

    cloudflare_zone = forms.ModelChoiceField(empty_label=None, queryset=None)
    captcha = TurnstileCaptchaField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['extra_info'].widget.attrs = {'rows': 3}

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
            Row(
                Div('inception_date', css_class='form-group col-md-6 mb-0'),
                Div('extra_info', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Div('captcha', css_class='form-group col-md-6 mb-0')
            ),
            ButtonHolder(
                Submit('submit', 'Submit'),
            )
        )

        self.fields['cloudflare_zone'].queryset = CloudflareZone.objects.filter(public=True)
        self.fields['cloudflare_zone'].label = "Partyman host"


class ActivationForm(ModelForm):
    class Meta:
        model = Request
        fields = ['party_name', 'contact_email', 'domain', 'cloudflare_zone', 'upcloud_zone',
                  'upcloud_plan']

    def _get_submit_button(self):
        if self.approved and not self.deactivated:
            return Submit('submit', 'Deactivate', css_class='btn btn-danger')
        if not self.approved and not self.deactivated:
            return Submit('submit', 'Activate')

    def __init__(self, *args, **kwargs):
        self.approved = kwargs.pop('approved', False)
        self.deactivated = kwargs.pop('deactivated', False)
        super().__init__(*args, **kwargs)

        self.fields['upcloud_zone'].widget.attrs.update({"autocomplete": "off"})
        self.fields['upcloud_plan'].widget.attrs.update({"autocomplete": "off"})

        if self.approved:
            self.fields['domain'].widget.attrs.update({"disabled": True})
            self.fields['cloudflare_zone'].widget.attrs.update({"disabled": True})
            self.fields['domain'].required = False
            self.fields['cloudflare_zone'].required = False
            self.fields['upcloud_zone'].widget.attrs.update({"disabled": True})
            self.fields['upcloud_plan'].widget.attrs.update({"disabled": True})

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Div('party_name', css_class='form-group col-md-6 mb-0'),
                Div('contact_email', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Div('domain', css_class='form-group col-md-6 mb-0'),
                Div('cloudflare_zone', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Div('upcloud_zone', css_class='form-group col-md-6 mb-0'),
                Div('upcloud_plan', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            ButtonHolder(
                self._get_submit_button()
            )
        )
