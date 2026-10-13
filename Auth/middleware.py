from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils import timezone


class IdleLogoutMiddleware:
    """Sign users out after `SESSION_IDLE_TIMEOUT` seconds without a request."""

    SESSION_KEY = "last_activity"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timeout = settings.SESSION_IDLE_TIMEOUT
        if timeout and request.user.is_authenticated:
            now = timezone.now().timestamp()
            last_activity = request.session.get(self.SESSION_KEY)
            if last_activity is not None and now - last_activity > timeout:
                logout(request)
                return redirect("account_login")
            request.session[self.SESSION_KEY] = now
        return self.get_response(request)
