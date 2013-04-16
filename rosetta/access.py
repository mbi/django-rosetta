from django.conf import settings
from django.utils import importlib


def can_translate(user):
    return get_access_control_function()(user)


def get_access_control_function():
    """
    Return a predicate for determining if a user can access the Rosetta views
    """
    fn_path = getattr(settings, 'ROSETTA_ACCESS_CONTROL_FUNCTION', None)
    if fn_path is None:
        return is_superuser_staff_or_in_translators_group
    # Dynamically load a permissions function
    perm_module, perm_func = fn_path.rsplit('.', 1)
    perm_module = importlib.import_module(perm_module)
    return getattr(perm_module, perm_func)


# Default access control test
def is_superuser_staff_or_in_translators_group(user):
    if not getattr(settings, 'ROSETTA_REQUIRES_AUTH', True):
        return True
    if not user.is_authenticated():
        return False
    elif user.is_superuser and user.is_staff:
        return True
    else:
        try:
            from django.contrib.auth.models import Group
            translators = Group.objects.get(name='translators')
            return translators in user.groups.all()
        except Group.DoesNotExist:
            return False
