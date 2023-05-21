import datetime
import logging

import dateparser
import requests_html

from trainonpolar.formatting import pace, duration, simple_title

logger = logging.getLogger(__name__)


def login(config):
    session = requests_html.HTMLSession()
    login_data = {
        'email': config["polarflow"]["email"],
        'password': config["polarflow"]["password"],
    }
    r = session.post(
        'https://flow.polar.com/login',
        data=login_data
    )
    if not r.url.startswith('https://flow.polar.com/diary'):
        logger.error("Cannot connect to Polar Flow: Login failed.")
        exit(1)
    logger.info("Login to Polar Flow succeeded.")
    return session


def phased_target_from_garmin(workout: dict, date: datetime.datetime):
    target = {
        "type": "PHASED",
        "name": simple_title(workout["workoutName"]),
        "description": "",
        "datetime": date.strftime("%Y-%m-%dT%H:%M"),
        "exerciseTargets": [{
            "id": None,
            "distance": None,
            "calories": None,
            "duration": None,
            "index": 0,
            "sportId": 1,  # running
            "phases": [phase_from_garmin(step) for step in workout["steps"]]
        }]
    }
    logger.debug(f"Converted workout to polar flow json format: {target}")
    return target


def phase_from_garmin(step: dict):
    if step["type"] == "WorkoutRepeatStep":
        return {
            "phaseType": "REPEAT",
            "repeatCount": int(step["repeatValue"]),
            "phases": [phase_from_garmin(s) for s in step["steps"]]
        }
    else:
        return {
            "id": None,
            "lowerZone": 1,
            "upperZone": 5,
            "intensityType": "SPEED_ZONES",
            "phaseChangeType": "AUTOMATIC",
            "goalType": ("DISTANCE"
                         if step["durationType"] == "DISTANCE"
                         else "DURATION"),
            "duration": ("00:00:00"
                         if step["durationType"] == "DISTANCE"
                         else duration(step["durationValue"])),
            "distance": (int(step["durationValue"])
                         if step["durationType"] == "DISTANCE"
                         else None),
            "name": f"{pace(step['targetValue'])}",
            "phaseType": "PHASE"
        }


def upload(session, target):
    r = session.post(
        "https://flow.polar.com/api/trainingtarget",
        json=target,
        headers={'X-Requested-With': 'XMLHttpRequest'})
    if r.status_code != 201:
        logger.error(f"Failed to upload workout to polar flow: {r.status_code}:\n{r.text}")
        return None
    else:
        logger.info("Uploaded workout to polar flow:"
                    f"https://flow.polar.com/target/{r.text}")
        return r.text


def check_conflicting_target(session, date):
    r = session.get(
        f"https://flow.polar.com/training/getCalendarEvents?start={date.strftime('%d.%m.%Y')}&end={(date+datetime.timedelta(days=1)).strftime('%d.%m.%Y')}",
        headers={'X-Requested-With': 'XMLHttpRequest'}
    )

    if r.status_code != 200:
        logger.warning(f"Failed to check for polar flow workouts on: {date}")
        logger.error(r.text)
        return None

    for item in r.json():
        if (item["type"] == "TRAININGTARGET" and
                dateparser.parse(item["datetime"]) == date):
            logger.debug("Found conflicting training target: "
                         f"https://flow.polar.com/target/{item['ListItemId']}")
            return item['ListItemId']
    return None
