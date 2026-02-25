from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import resolve_url


def is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


def htmx_redirect(url: str, status: int = 204) -> HttpResponse:
    response = HttpResponse(status=status)
    response["HX-Redirect"] = url
    return response


def login_redirect_url(request) -> str:
    from django.shortcuts import resolve_url
    from django.conf import settings
    login_url = resolve_url(settings.LOGIN_URL)
    next_url = request.headers.get("HX-Current-URL") or request.get_full_path()
    return f"{login_url}?{urlencode({'next': next_url})}"
