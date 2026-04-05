from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


class DeactivatedUserMiddleware:
    """
    Checks on every request whether the logged-in user's is_active flag
    is still True. If the admin has deactivated them since they logged in,
    their session is immediately destroyed and they are sent to the login page.
    """

    # URLs that deactivated users are allowed to visit (so they don't loop)
    ALLOWED_PATHS = {
        reverse('login'),
        reverse('contact_admin'),
        '/static/',
        '/media/',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Re-fetch is_active fresh from the DB on every request
            # (request.user is cached from the session — it won't reflect
            #  changes made by the admin after the user logged in)
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                fresh = User.objects.only('is_active').get(pk=request.user.pk)
                if not fresh.is_active:
                    logout(request)
                    messages.warning(
                        request,
                        'Your account has been deactivated by the administrator. '
                        'Please contact the admin to reactivate your account.'
                    )
                    return redirect('login')
            except User.DoesNotExist:
                logout(request)
                return redirect('login')

        return self.get_response(request)
