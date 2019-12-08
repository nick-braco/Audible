import logging
from asyncio import get_event_loop
from functools import wraps
from inspect import isawaitable
import time


class ElapsedTime:
    """Time measurement
    
    :example:

    >>> et = ElapsedTime()
    >>> time_marker_1 = et()
    >>> time_marker_2 = et()

    """
    def __init__(self):
        self.start_time = time.time()

    def __call__(self):
        return time.time() - self.start_time


# copied from https://github.com/maas/python-libmaas
def asynchronous(func):
    """Return `func` in a "smart" asynchronous-aware wrapper.
    If `func` is called within the event-loop — i.e. when it is running — this
    returns the result of `func` without alteration. However, when called from
    outside of the event-loop, and the result is awaitable, the result will be
    passed though the current event-loop's `run_until_complete` method.
    In other words, this automatically blocks when calling an asynchronous
    function from outside of the event-loop, and so makes interactive use of
    these APIs far more intuitive.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        eventloop = get_event_loop()
        result = func(*args, **kwargs)
        if not eventloop.is_running():
            while isawaitable(result):
                result = eventloop.run_until_complete(result)
        return result

    return wrapper

