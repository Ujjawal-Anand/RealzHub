from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
from django.urls import URLPattern, reverse_lazy

from realzhub.core.views.decorators import permssions_required


class AppConfigMixin(object):
    """
    Base app configuration, used to extend
    :py:class `django.apps.AppConfig`
    to also provide URL configurations and mixins
    """

    # Instance namespace for the URLs
    namespace = None
    login_url = None

    #: Maps view names lists of permssions. Expects tuples of
    #: lists as dictionary values.  A list is a set of permissions that all
    #: need to be fullfilled (AND). Only one set of permssions has to be
    #: fulfilled (OR)
    #: If there's only one set of permissions, as a shortcut, you can
    #: just define one list
    permissions_map = {}

    #: Default permssion for any view not in permssions_map
    default_permissions = None

    def __init__(self, app_name, app_module, namespace=None, **kwargs):
        """
        kwargs:
            namespace: optionally specify the URL instance namepace
        """

        app_config_attrs = [
            "name",
            "module",
            "apps",
            "label",
            "verbose_name",
            "path",
            "models_module",
            "models",
        ]

        # To ensure sub classes do not add kwrgs that are used by
        # :py:class: `django.apps.AppConfig`
        clashing_kwargs = set(kwargs).intersection(app_config_attrs)
        if clashing_kwargs:
            raise ImproperlyConfigured(
                "Passes in kwargs can't be named the same as properties of"
                "AppConfig; clashing: %s" % ", ".join(clashing_kwargs)
            )

        super().__init__(app_name, app_module)

        if namespace is not None:
            self.namespace = namespace

        # set all kwargs as object attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_urls(self):
        """
        Return the URL patterns for this app
        """
        return []

    def post_process_urls(self, urlpatters):
        """
        Customize URL patterns

        This method allows decorators to be wrapped around an
        apps URL patterns.
        """

        for pattern in urlpatters:
            if hasattr(pattern, "url_patterns"):
                self.post_process_urls(pattern.url_patterns)

            if isinstance(pattern, URLPattern):
                # Apply the custom view decorator (if nay) set for
                # this class is a URL pattern
                decorator = self.get_url_decorator(pattern)
                if decorator:
                    pattern.callback = decorator(pattern.callback)

        return urlpatters

    def get_permissions(self, url):
        """
        Return a list of permssions for a given URL name

        Args:
        url (str): A URL name (e.g., ``users:index``)

        Returns:
            list: A list of permission strings
        """

        # url namespaced?
        if url is not None and ":" in url:
            view_name = url.split(":")[1]
        else:
            view_name = url

        return self.permissions_map.get(view_name, self.default_permissions)

    def get_url_decorator(self, pattern):
        """
        Return the appropriate decorator for the new view functions
        with the passed URL name, mainly used for access-protecting
        views

        It's possible to specify:
        - no permssions necessary: use None
        - a set of permssions: use a list
        - two set of permissons (`or`): use two-tuple of lists

        see permssion_required decorator for details
        """
        permissions = self.get_permissions(pattern.name)
        if permissions:
            return permssions_required(permissions, login_url=self.login_url)

    @property
    def urls(self):
        # we get the application and instance namespace here
        return self.get_urls(), self.label, self.namespace


class RealzHubConfig(AppConfigMixin, AppConfig):
    """
    Base app configuration

    This is subclassed by each app to provide a customizable
    container for its configuration, URL configuartions, and permssions
    """


class AppDashboardConfig(AppConfig):
    """
    Base app configuration for dashboard apps
    """

    login_url = reverse_lazy("dashboard:login")
