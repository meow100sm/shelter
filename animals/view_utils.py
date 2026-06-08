from __future__ import annotations

from django.shortcuts import redirect


def get_next_url(request, *, default: str = "") -> str:
    """Get `next` from POST or GET with a fallback default."""
    next_url = (request.POST.get("next") or request.GET.get("next") or default or "").strip()
    return next_url


def redirect_next_or(next_url: str, fallback_url: str):
    return redirect(next_url) if next_url else redirect(fallback_url)
