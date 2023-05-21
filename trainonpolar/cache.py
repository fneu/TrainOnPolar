import json
import os


def save(workout, id):
    with open("cache.json", "w") as f:
        json.dump({"id": id, "workout": workout}, f)


def is_unchanged(workout, id):
    if not os.path.exists("cache.json"):
        return False

    with open("cache.json", "r") as f:
        cache = json.load(f)
        return id == cache["id"] and workout == cache["workout"]
