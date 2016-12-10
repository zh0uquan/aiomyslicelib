"""
Exception class.

Errors happens in MySliceLib
"""
import ssl

__all__ = (
    'MySliceLibSetupError', 'MySliceLibSSLError'
)


class MySliceLibException(Exception):
    """
    Base error class for all MySliceLib Exception.
    """
    def __init__(self, message: str) -> None:
        self.message = message


class MySliceLibSetupError(MySliceLibException, ValueError):
    """
    The configuration was not settled as excepted
    """
    pass


class MySliceLibSSLError(MySliceLibException, ssl.SSLError):
    """
    An error occurrs when loading a cert/key in ssl context.
    """
    pass
