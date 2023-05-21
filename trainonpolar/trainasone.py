import logging

import dateparser
import requests_html

logger = logging.getLogger(__name__)


def login(config):
    session = requests_html.HTMLSession()
    login_data = {
        'email': config["trainasone"]["email"],
        'password': config["trainasone"]["password"],
    }
    r = session.post(
        'https://beta.trainasone.com/login',
        data=login_data
    )
    if not r.url.startswith('https://beta.trainasone.com/home'):
        logger.error("Cannot connect to TrainAsOne: Login failed.")
        exit(1)
    logger.info("Login to TrainAsOne succeeded.")
    return session


def next_run(session):
    r = session.get("https://beta.trainasone.com/calendarView")
    future_days = r.html.find(".today, .future")
    for day in future_days:
        if day.find(".workout"):
            url = day.find(
                ".workout a",
                first=True
            ).absolute_links.pop().replace(
                "plannedWorkout?",
                "plannedWorkoutDownload?sourceFormat=GARMIN_TRAINING&"
            )
            # time is set to 23:59:59.999999 to make sure that the
            # polar workout is due in the future
            date = dateparser.parse(
                day.find(".title", first=True).text
            ).replace(hour=23, minute=59, second=0, microsecond=0)
            logger.info(f"Found next workout on {date.strftime('%Y-%m-%d')}")
            logger.debug(f"Url to next workout: {url}")
            return url, date
    logger.error("Cannot find next workout in calendar view.")
    exit(1)


def get_workout(session, url):
    try:
        r = session.get(
            url,
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        content = r.json()
        logger.debug(f"Downloaded workout as garmin json: {content}")
        return content
    except Exception as e:
        logger.error(f"Cannot fetch or parse workout from TrainAsOne: {e}")
        exit(1)
