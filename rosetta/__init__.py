__version__ = "0.10.5"

VERSION = tuple(int(part) for part in __version__.split("."))


def get_version(limit=3):
    """Return the version as a human-format string."""
    return ".".join([str(i) for i in VERSION[:limit]])
