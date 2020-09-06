from django.urls import path
from django.utils.translation import gettext_lazy as _

from realzhub.core.application import RealzHubConfig
from realzhub.core.loading import get_class


class UsersConfig(RealzHubConfig):
    label = "users"
    name = "realzhub.apps.users"
    verbose_name = _("Users")

    def ready(self):
        try:
            import realzhub.apps.users.signals  # noqa F401
        except ImportError:
            pass

        self.user_redirect_view = get_class("users.views", "UserRedirectView").as_view()
        self.user_update_view = get_class("users.views", "UserUpdateView").as_view()
        self.user_detail_view = get_class("users.views", "UserDetailView").as_view()

    def get_urls(self):
        urls = [
            path("~redirect/", view=self.user_redirect_view, name="redirect"),
            path("~update/", view=self.user_update_view, name="update"),
            path("<str:username>/", view=self.user_detail_view, name="detail"),
        ]
        return self.post_process_urls(urls)
