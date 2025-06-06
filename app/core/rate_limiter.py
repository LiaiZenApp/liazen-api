import inspect
from functools import wraps
from typing import Callable

from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def rate_limit(limit_str: str) -> Callable:
    """
    A decorator to apply a rate limit at request‐time. It does the following:
    
    1. Calls `limiter.limit(limit_str)` to get back a decorator.
    2. Immediately applies that decorator to the original endpoint function.
    3. Invokes the decorated function. If RateLimitExceeded is raised, it bubbles
       up so that FastAPI's exception‐handler for RateLimitExceeded (or your custom
       handler) can turn it into a 429.
    """

    def decorator(endpoint: Callable):
        @wraps(endpoint)
        async def wrapper(request: Request, *args, **kwargs):

            global limiter

            try:
                slow_decorator = limiter.limit(limit_str)
            except RateLimitExceeded as e:
                raise

            decorated = slow_decorator(endpoint)

            result = decorated(request, *args, **kwargs)

            if inspect.isawaitable(result):
                return await result
            return result

        return wrapper

    return decorator