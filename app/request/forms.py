from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Row, Div, ButtonHolder, Submit
from django_cf_turnstile.fields import TurnstileCaptchaField
from django import forms
from django.forms import ModelForm
from .models import Request, CloudflareZone


def _password_field():
    return forms.TextInput(attrs={"type": "password", "autocomplete": "current-password"})


class AppSettingsForm(ModelForm):
    class Meta:
        model = Request
        fields = '__all__'
        widgets = {
            "upcloud_api_password": _password_field(),
            "cloudflare_api_token": _password_field(),
            "cloudflare_turnstile_secret": _password_field(),
            "mailjet_api_secret": _password_field()
        }


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

    def __init__(self, *args, **kwargs):
        self.approved = kwargs.pop('approved', False)
        self.deactivated = kwargs.pop('deactivated', False)
        super().__init__(*args, **kwargs)

        self.fields['upcloud_zone'].widget.attrs.update({"autocomplete": "off"})
        self.fields['upcloud_zone'].required = True
        self.fields['upcloud_plan'].widget.attrs.update({"autocomplete": "off"})
        self.fields['upcloud_plan'].required = True

        if self.approved:
            self.fields['domain'].disabled = True
            self.fields['cloudflare_zone'].disabled = True
            self.fields['upcloud_zone'].disabled = True
            self.fields['upcloud_plan'].disabled = True

        self.helper = FormHelper()
        self.helper.form_tag = False
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
            )
        )
