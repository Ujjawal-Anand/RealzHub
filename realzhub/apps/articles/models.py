from django.db import models
from django.utils.translation import gettext_lazy as _

from realzhub.core.base_models import ModelWithMetadata, TimestampedModel

# Create your models here.


class Article(TimestampedModel, ModelWithMetadata):
    """
    Article Model class
    """

    title = models.CharField(
        _("title"), max_length=253, help_text=_("title of article")
    )
    image = models.URLField(
        _("Image Url"),
        null=True,
        blank=True,
        help_text=_("The url of image to be fetched"),
    )
    article_url = models.URLField(
        _("Url"), help_text=_("url of article to be redirected to read full article")
    )

    def __str__(self):
        return self.title


class Source(TimestampedModel, ModelWithMetadata):
    """
    Source model from where articles will be fetched
    """

    name = models.CharField(_("Source Name"), max_length=253)
    feed_url = models.URLField(
        _("Feed Url"), help_text=_("Feed url from where the articles will be fetched")
    )
    fetched_at = models.DateTimeField(
        _("Fetchd At"),
        null=True,
        blank=True,
        help_text=_("Time when articles were fetched last time"),
    )
