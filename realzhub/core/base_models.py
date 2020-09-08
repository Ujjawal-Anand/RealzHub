from typing import Any

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimestampedModel(models.Model):
    """
    An abstract class to be extended to add timestamp to models
    """

    # auto_now_add will set the timezone.now() only when the instance is created
    created_at = models.DateTimeField(
        _("datetime when model is created"), auto_now_add=True
    )
    # auto_now will update the field everytime the save method is called.
    update_at = models.DateTimeField(
        _("datetime when model is updated last time"), auto_now=True
    )

    class Meta:
        abstract = True


class ModelWithMetadata(models.Model):
    """
    An abstract class to be extended to add metadata to models
    """

    metadata = JSONField(
        _("used to store metadata"), blank=True, null=True, default=dict
    )

    class Meta:
        abstract = True

    def get_value_from_metadata(self, key, default: Any = None) -> Any:
        return self.metadata.get(key, default)

    def store_value_in_metadata(self, items: dict):
        if not self.metadata:
            self.metadata = {}
        self.metadata.update(items)

    def append_value_in_metadata(self, key: str, value):
        # if metadata is None or key not in metadata
        if key not in self.metadata:
            self.store_value_in_metadata({key: [value]})
        # if value is not a list
        elif not isinstance(self.get_value_from_metadata(key), list):
            # create a list with existing and new data
            value_list = list(self.get_value_from_metadata(key), value)
            # add the dict
            self.store_value_in_metadata({key: value_list})
        else:
            value_list = self.get_value_from_metadata(key).append(value)

    def clear_metadata(self):
        self.metadata = {}

    def delete_value_from_metadata(self, key: str):
        if key in self.metadata:
            del self.metadata[key]
