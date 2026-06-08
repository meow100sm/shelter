from __future__ import annotations

from typing import Callable

from django.contrib.auth.decorators import user_passes_test


def has_role(user, *roles: str) -> bool:
    return bool(user and user.is_authenticated and user.role in roles)


def role_required(*roles: str) -> Callable:
    """Restrict a view to authenticated users with any of the given roles."""

    def check(user) -> bool:
        return has_role(user, *roles)

    return user_passes_test(check)


def is_admin(user) -> bool:
    return has_role(user, "admin")


def is_vet(user) -> bool:
    return has_role(user, "admin", "vet")


def is_volunteer(user) -> bool:
    return has_role(user, "admin", "vet", "volunteer")
