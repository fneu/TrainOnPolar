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


def phased_target_from_garmin(workout: dict, date: datetime.datetime, zones_lower_bounds):
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
            "phases": [phase_from_garmin(step, zones_lower_bounds) for step in workout["steps"]]
        }]
    }
    logger.debug(f"Converted workout to polar flow json format: {target}")
    return target


def phase_from_garmin(step: dict, zones_lower_bounds):
    if step["type"] == "WorkoutRepeatStep":
        return {
            "phaseType": "REPEAT",
            "repeatCount": int(step["repeatValue"]),
            "phases": [phase_from_garmin(s, zones_lower_bounds) for s in step["steps"]]
        }
    else:
        return {
            "id": None,
            "lowerZone": get_zone(step, zones_lower_bounds),
            "upperZone": get_zone(step, zones_lower_bounds),
            "intensityType": ("SPEED_ZONES"
                              if step["targetType"] == "SPEED"
                              else "NONE"),
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
            "name": (f"{pace(step['targetValue'])}"
                     if step["targetType"] == "SPEED"
                     else step["description"]),
            "phaseType": "PHASE"
        }


def get_zone(step, bounds):
    if step["targetType"] != "SPEED":
        return None
    for i, b in enumerate(bounds):
        if step['targetValue']*3.6 < b:
            if i == 0:
                logger.warning("step target is lower than speed zone 1")
                return 1
            return i
    return 5


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


def delete(session, id):
    r = session.delete(
        f"https://flow.polar.com/training/target/{id}",
        headers={'X-Requested-With': 'XMLHttpRequest'})

    if r.status_code == 200:
        logger.warning("Deleted a previously uploaded training target that was scheduled for the same time.")
    else:
        logger.warning(f"Failed to delete https://flow.polar.com/target/{id}")


def check_conflicting_target(session, date):
    r = session.get(
        f"https://flow.polar.com/training/getCalendarEvents?start={date.strftime('%d.%m.%Y')}&end={(date+datetime.timedelta(days=1)).strftime('%d.%m.%Y')}",
        headers={'X-Requested-With': 'XMLHttpRequest'}
    )

    if r.status_code != 200:
        logger.warning(f"Failed to check for polar flow workouts on: {date}")
        return None

    for item in r.json():
        if (item["type"] == "TRAININGTARGET" and
                dateparser.parse(item["datetime"]) == date):
            logger.debug("Found conflicting training target: "
                         f"https://flow.polar.com/target/{item['ListItemId']}")
            return item['ListItemId']
    return None


def find_running_profile(session):
    r = session.get("https://flow.polar.com/settings/sports")
    sports = r.html.find(".sportProfile-item")
    for sport in sports:
        if sport.attrs["data-sport-id"] == "1":  # running
            logger.debug(f"running sport profile has id {sport.attrs['data-profile-id']}")
            return sport.attrs["data-profile-id"]
    logger.warning("Could not find running sport profile")
    return None


def set_zones(session, config, lower_bounds):
    assert len(lower_bounds) == 5

    r = session.post(
        "https://flow.polar.com/settings/sports/save",
        json={
            "sports": {
                find_running_profile(session): [
                    {
                        "name": "SpeedSettings",
                        "settings": [
                            {
                                "name": "measurementUnit",
                                "value": config['zones']['measurement_unit']
                            },
                            {
                                "name": "speedViewMode",
                                "value": config['zones']['speed_view_mode']
                            },
                            {
                                "name": "masEstimated",
                                "value": config.getboolean('zones', 'mas_estimated')
                            },
                            {
                                "name": "mas",
                                "value": config['zones']['mas']
                            },
                            {
                                "name": "speedZoneType",
                                "value": "FREE"
                            },
                            {
                                "name": "freeSpeedZone1Min",
                                "value": str(lower_bounds[0])
                            },
                            {
                                "name": "freeSpeedZone2Min",
                                "value": str(lower_bounds[1])
                            },
                            {
                                "name": "freeSpeedZone3Min",
                                "value": str(lower_bounds[2])
                            },
                            {
                                "name": "freeSpeedZone4Min",
                                "value": str(lower_bounds[3])
                            },
                            {
                                "name": "freeSpeedZone5Min",
                                "value": str(lower_bounds[4])
                            },
                        ]
                    }
                ]
            }
        },
        headers={'X-Requested-With': 'XMLHttpRequest'})
    logger.info(f"Zone change return code: {r.status_code}")
    logger.info(f"Zone change return message: {r.text}")
