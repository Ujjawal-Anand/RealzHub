from django.apps import apps
from django.urls import path
from django.views.generic import TemplateView

from realzhub.core.application import RealzHubConfig


class RealzHub(RealzHubConfig):
    name = "realzhub"

    def ready(self):
        self.users_app = apps.get_app_config("users")

    def get_urls(self):

        urls = [
            path("users/", self.users_app.urls),
            path(
                "", TemplateView.as_view(template_name="pages/home.html"), name="home"
            ),
            path(
                "about/",
                TemplateView.as_view(template_name="pages/about.html"),
                name="about",
            ),
        ]
        return urls
