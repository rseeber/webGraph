import json
import traceback
import inspect
import glob

def globTest():
    print(glob.glob("data/data-archived/*.json"))


def foo(maxCount, count=0):
    x = inspect.stack()
    print(x)

    # RECURSIVE CASE
    if count < maxCount:
        print()
        foo(count+1, maxCount)
    # BASE CASE
    return

def accessVar():
    print(x)

globTest()