class BaseRosettaStorage:
    def __repr__(self):
        return str(self.id)

    def __del__(self):
        self._persist(self.__dict__)

    def __getattr__(self, key, *args, **kwargs):
        return None

    def __getitem__(self, key):
        return self.__dict__.get(key, None)

    def __iter__(self):
        return self.__dict__.__iter__()


class SessionRosettaStorage(BaseRosettaStorage):
    def __init__(self, request):
        self.request = request

        for key, value in self.request.session.iteritems():
            if key.startswith('rosetta_'):
                setattr(self, key, value)

    def _persist(self, what):
        for key, value in what:
            if key.startswith('rosetta_'):
                self.request.session[key] = value
