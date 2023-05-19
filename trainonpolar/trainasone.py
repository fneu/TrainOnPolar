import logging

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
    logger.debug("Login to TrainAsOne succeeded.")
    return session
