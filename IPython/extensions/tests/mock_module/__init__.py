__author__ = 'USER'

RETURN_VALUE = 15


class BaseMock(object):
    @classmethod
    def get(cls, **kwargs):
        return RETURN_VALUE


class NotBaseMock(object):
    pass


class BaseMockSup(BaseMock):
    pass