VERSION = (0, 7, 13)
default_app_config = "rosetta.apps.RosettaAppConfig"


def get_version(svn=False, limit=3):
    """Return the version as a human-format string."""
    return '.'.join([str(i) for i in VERSION[:limit]])
