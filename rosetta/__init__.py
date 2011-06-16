VERSION = (0, 6, 2)

def get_version(svn=False, limit=3):
    "Returns the version as a human-format string."
    v = '.'.join([str(i) for i in VERSION[:limit]])
    if svn and limit >= 3:
        from django.utils.version import get_svn_revision
        import os
        svn_rev = get_svn_revision(os.path.dirname(__file__))
        if svn_rev:
            v = '%s.%s' % (v, svn_rev)
    return v
