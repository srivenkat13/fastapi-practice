"""P3 reference solution."""
import functools


def build_query(path, *, sort=None, **filters):
    params = {k: v for k, v in filters.items() if v is not None}
    if sort is not None:
        params["sort"] = sort
    if not params:
        return path
    return path + "?" + "&".join(f"{k}={params[k]}" for k in sorted(params))


def append_tag(tag, tags=None):
    tags = [] if tags is None else tags
    tags.append(tag)
    return tags


def make_counter(start=0):
    count = start

    def inc():
        nonlocal count
        count += 1
        return count

    return inc


def retry(times, exceptions=(Exception,)):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_error = None
            for _ in range(times):
                try:
                    return fn(*args, **kwargs)
                except exceptions as error:
                    last_error = error
            raise last_error

        return wrapper

    return decorator


def memoize(fn):
    cache = {}

    @functools.wraps(fn)
    def wrapper(*args):
        if args not in cache:
            cache[args] = fn(*args)
        return cache[args]

    wrapper.cache = cache
    return wrapper


ROUTES = {}


def register(path):
    def decorator(fn):
        ROUTES[path] = fn
        return fn

    return decorator
