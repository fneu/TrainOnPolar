import json
import logging
import os

logger = logging.getLogger(__name__)

def save(workout, id):
    with open("cache.json", "w") as f:
        json.dump({"id": id, "workout": workout}, f)


def is_unchanged(workout, id):
    if not os.path.exists("cache.json"):
        return False

    with open("cache.json", "r") as f:
        cache = json.load(f)
        result = str(id) == str(cache["id"]) and workout == cache["workout"]
        if result:
            logger.debug(f"{id} is the last uploaded id and TAO workout is unchanged.")
        else:
            logger.debug(f"{id} is an unknown id or TAO workout changed")

        return result

