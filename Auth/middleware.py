from django.utils import timezone
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect

class AutoLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the user is authenticated
        try:
            if request.user.is_authenticated and not request.user.is_superuser :
                # Get the last activity time from the session
                last_activity = request.session.get('last_activity')

                # If last_activity is not set, set it to now
                if last_activity is None:
                    request.session['last_activity'] = timezone.now().timestamp()
                else:
                    # Check if the user has been inactive for too long
                    if timezone.now().timestamp() - last_activity > settings.SESSION_COOKIE_AGE:
                        logout(request)  # Log out the user
                        del request.session['last_activity']  # Clear the last activity time
                        return redirect('home')  # Redirect to the login page

                    # Update the last activity time
                    request.session['last_activity'] = timezone.now().timestamp()
            else:
                pass
        except:
            redirect("home")
        response = self.get_response(request)
        return response
