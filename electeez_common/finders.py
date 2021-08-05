from django.contrib.staticfiles.finders import BaseFinder
from django.contrib.staticfiles.storage import staticfiles_storage

class StaticRootFinder(BaseFinder):
    """
    For debug mode only. Serves files from STATIC_ROOT.
    """
    def find(self, path, all=False):
        full_path = staticfiles_storage.path(path)
        if staticfiles_storage.exists(full_path):
            return [full_path] if all else full_path
        return []

    def list(self, ignore_patterns):
        return iter(())
