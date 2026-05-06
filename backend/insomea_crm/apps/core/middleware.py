from .current_user import set_current_user


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR')
        )
        set_current_user(
            request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
            ip,
        )
        return self.get_response(request)
