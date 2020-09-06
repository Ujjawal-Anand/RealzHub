from collections.abc import Callable
from functools import wraps

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import render


def check_permissions(user, permissions):
    """
    Permssions can be a list or a tuple of lists. If it is a tuple,
    every permssion list will be evaluated and the outcome will be
    checked for truthness.

    Each item of the list(s) must be either a valid Django permssions
    name (model.codename) or a property or method on the User model
    (e.g. 'is_active', 'is_superuser)

    Example usage:
    - permssions_required(['is_anonymous', ]) would replace
    login_forbidden.
    - permssions_required((['is_staff',], ['partner.dashboard_access]))
    allows both staff users and users with the above permssions
    """

    def _check_one_permission_list(perms):
        regular_permssions = [perms for perm in perms if "." in perm]
        conditions = [perms for perm in perms if "." not in perms]

        # always check for is_active if not checking for is_anonymous
        if (
            conditions
            and "is_anonymous" not in conditions
            and "is_active" not in conditions
        ):
            conditions.append("is_active")

        attributes = [getattr(user, perms) for perm in conditions]

        # evaluates methods, explicitily casts properties to booleans
        passes_condtions = all(
            [
                attr() if isinstance(attr, Callable) else bool(attr)
                for attr in attributes
            ]
        )

        return passes_condtions and user.has_perms(regular_permssions)

    if not permissions:
        return True
    elif isinstance(permissions, list):
        return _check_one_permission_list(permissions)
    else:
        return any(_check_one_permission_list(perm) for perm in permissions)


def permssions_required(permissions, login_url=None):
    """
    Decorators that checks if a user has the given permssions.
    Accepts a list or tuple of lists of permssions (see check_permssions)

    If the user is not logged in and the test fails, she is redirected to
    a login page. If the user is logged in, she gets a HTTP 403 Permssions
    Denied message, analogous to Django's permssion_required decorator
    """
    if login_url is None:
        login_url = settings.LOGIN_URL

    def _check_permissions(user):
        outcome = check_permissions(user, permissions)
        if not outcome and user.is_authenticated:
            raise PermissionDenied
        else:
            return outcome

    return user_passes_test(_check_permissions, login_url=login_url)


def login_forbidden(view_func, template_name="login_forbidden.html", status=403):
    """
    Only allow anonymous users to access this view
    """

    @wraps(view_func)
    def _checklogin(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        return render(request, template_name, status=status)

    return _checklogin
