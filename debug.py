import json


cache = {"a": 1, "b": 2, "c": 3}

print(json.dumps(cache))

print(len(json.dumps(cache)))

input()