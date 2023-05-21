import json
import logging
import os

logger = logging.getLogger(__name__)


def save(workout, id):
    with open("cache.json", "w") as f:
        json.dump({"id": id, "workout": workout}, f)


def tao_unchanged(workout):
    if not os.path.exists("cache.json"):
        return False
    with open("cache.json", "r") as f:
        cache = json.load(f)
        result = workout == cache["workout"]
    if result:
        logger.debug("TAO workout is unchanged.")
    else:
        logger.debug("TAO workout changed")

    return result


def is_last_uploaded(id):
    if not os.path.exists("cache.json"):
        return False

    with open("cache.json", "r") as f:
        cache = json.load(f)
        result = str(id) == str(cache["id"])
    if result:
        logger.debug(f"{id} is the last uploaded id")
    else:
        logger.debug(f"{id} is an unknown id")

    return result
