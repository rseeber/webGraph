import json
import traceback
import inspect


def foo(maxCount, count=0):
    x = inspect.stack()
    print(x)

    # RECURSIVE CASE
    if count < maxCount:
        print()
        foo(count+1, maxCount)
    # BASE CASE
    return

foo(1)