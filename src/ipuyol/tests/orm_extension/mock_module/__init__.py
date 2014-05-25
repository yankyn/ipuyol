__author__ = 'USER'

RETURN_VALUE = 15

class BaseMetaClass(type):
    pass

class BaseMock(object):

    __metaclass__ = BaseMetaClass

    @classmethod
    def get(cls, **kwargs):
        return RETURN_VALUE


class NotBaseMock(object):
    pass


class BaseMockSup(BaseMock):
    pass