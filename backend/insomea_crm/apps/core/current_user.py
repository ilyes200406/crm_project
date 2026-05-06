from contextvars import ContextVar

_current_user: ContextVar = ContextVar("current_user", default=None)
_current_ip: ContextVar = ContextVar("current_ip", default=None)


def set_current_user(user, ip=None):
    _current_user.set(user)
    _current_ip.set(ip)


def get_current_user():
    return _current_user.get()


def get_current_ip():
    return _current_ip.get()
