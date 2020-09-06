import sys
import traceback
from functools import lru_cache
from importlib import import_module

from django.apps import apps
from django.apps.config import MODELS_MODULE_NAME
from django.conf import settings
from django.core.exceptions import AppRegistryNotReady
from django.utils.module_loading import import_string

from realzhub.core.exceptions import AppNotFoundError, ClassNotFoundError


def get_class(module_label, classname, module_prefix="realzhub.apps"):
    """
    Dynamically import a single class from the given module

    This is a single wrapper around `get_classes` for the case of
    loading a single class
    """
    return get_classes(module_label, [classname], module_prefix)[0]


@lru_cache(maxsize=100)
def get_class_loader():
    return import_string(settings.DYNAMIC_CLASS_LOADER)


def get_classes(module_label, classnames, module_prefix="relazhub.apps"):
    class_loader = get_class_loader()
    return class_loader(module_label, classnames, module_prefix)


def get_model(app_label, model_name):
    """
    Fetches a Django model using the app registery.

    All other methods to acces models might raise an exception about
    registery not being ready yet.

    This doesn't require that an app with the given app label exists,
    which makes it safe to call when the registery is being populated.

    Raises LookupError if model isn't found
    """
    try:
        return apps.get_model(app_label, model_name)
    except AppRegistryNotReady:
        if apps.apps_ready and not apps.models_ready:
            # if this function is called while `apps.populate()` is
            # loading models, ensure that the module thar defines
            # the target model has been imorted and try looking the
            # model up in the app registery. This effectiveness emulates
            # `from path.to.app.models import Model` where we use
            # `Model = get_model('app', 'Model')` instead
            app_config = apps.get_app_config(app_label)
            # `app_config.import_models()` cannot be used here because
            # it would interfere with `app.populate()`
            import_module("%s.%s" % (app_config.name, MODELS_MODULE_NAME))
            # In order to account for case-insensitivity of model_name,
            # look up the model through a private API of the app registry.
            return apps.get_registered_model(app_label, model_name)
        else:
            # This must be a different case (e.g. the model really doesn't
            # exist). We just re-raise the exception.
            raise


def default_class_loader(module_lable, classnames, module_prefix):
    """
    Dynamically import a list of classes from the given module.

    This works by looking up a matching app from the app registry,
    against the passed module label.  If the requested class can't be found in
    the matching module, then we attempt to import it from the corresponding
    core app.
    """

    if "." not in module_lable:
        # Importing from top-level modules is not supported
        raise ValueError("Importing from top-level modules is not supported")

    # import from realzhub package (should succeed in most case)
    # e.g. `realzhub.apps.users.forms`
    realzhub_module_lable = "%s.%s" % (module_prefix, module_lable)
    realzhub_module = _import_module(realzhub_module_lable, classnames)

    # returns e.g. 'champsquarebackend.apps.dashboard.catalogue',
    # 'yourproject.apps.dashboard.catalogue' or 'dashboard.catalogue',
    # depending on what is set in INSTALLED_APPS
    app_name = _find_registered_app_name(module_lable)
    if app_name.startswith("%s." % module_prefix):
        # The entry is obviously an champsquarebackend one, we don't import again
        local_module = None
    else:
        # Attempt to import the classes from the local module
        # e.g. 'yourproject.dashboard.catalogue.forms'
        local_module_label = ".".join(app_name.split(".") + module_lable.split(".")[1:])
        local_module = _import_module(local_module_label, classnames)

    if realzhub_module is local_module is None:
        # This intentionally doesn't raise an ImportError, because ImportError
        # can get masked in complex circular import scenarios.
        raise ModuleNotFoundError(
            "The module with label '%s' could not be imported. This either"
            "means that it indeed does not exist, or you might have a problem"
            " with a circular import." % module_lable
        )

    # return imported classes, giving preference to ones from the local package
    return _pluck_classes([local_module, realzhub_module], classnames)


def _import_module(module_label, classnames):
    """
    Imports the module with the given name.
    Returns None if the module doesn't exist, but propagates any import errors.
    """
    try:
        return __import__(module_label, fromlist=classnames)
    except ImportError:
        # There are 2 reasons why there could be an ImportError:
        #
        #  1. Module does not exist. In that case, we ignore the import and
        #     return None
        #  2. Module exists but another ImportError occurred when trying to
        #     import the module. In that case, it is important to propagate the
        #     error.
        #
        # ImportError does not provide easy way to distinguish those two cases.
        # Fortunately, the traceback of the ImportError starts at __import__
        # statement. If the traceback has more than one frame, it means that
        # application was found and ImportError originates within the local app
        __, __, exc_traceback = sys.exc_info()
        frames = traceback.extract_tb(exc_traceback)
        if len(frames) > 1:
            raise


def _pluck_classes(modules, classnames):
    """
    Gets a list of class names and a list of modules to pick from.
    For each class name, will return the class from the first module that has a
    matching class.
    """
    klasses = []
    for classname in classnames:
        klass = None
        for module in modules:
            if hasattr(module, classname):
                klass = getattr(module, classname)
                break
        if not klass:
            packages = [m.__name__ for m in modules if m is not None]
            raise ClassNotFoundError(
                "No class '%s' found in %s" % (classname, ", ".join(packages))
            )
        klasses.append(klass)
    return klasses


def _find_registered_app_name(module_label):
    """
    Given a module label, finds the name of the matching champsquarebackend app from the
    Django app registry.
    """
    from realzhub.core.application import AppConfig

    app_label = module_label.split(".")[0]
    try:
        app_config = apps.get_app_config(app_label)
    except LookupError:
        raise AppNotFoundError("Couldn't find an app to import %s from" % module_label)
    if not isinstance(app_config, AppConfig):
        raise AppNotFoundError(
            "Couldn't find an champsquarebackend app to import %s from" % module_label
        )
    return app_config.name
