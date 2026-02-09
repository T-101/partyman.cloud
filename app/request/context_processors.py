from request.models import AppSettings


def app_settings_context(request):
    return {
        'app_settings': AppSettings.load()
    }
