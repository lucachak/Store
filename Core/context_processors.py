from django.conf import settings

# URL prefix -> section of the app shell that should look "current".
NAV_SECTIONS = (
    ("/subscription/billing", "billing"),
    ("/subscription", "plans"),
    ("/dashboard", "overview"),
    ("/accounts/", "account"),
    ("/auth/settings", "account"),
    ("/auth/users", "users"),
)


def site(request):
    """Values every template needs: product name, billing state, active nav section."""
    section = ""
    for prefix, name in NAV_SECTIONS:
        if request.path.startswith(prefix):
            section = name
            break
    return {
        "SITE_NAME": settings.SITE_NAME,
        "BILLING_ENABLED": bool(settings.STRIPE_SECRET_KEY),
        "nav_section": section,
    }
