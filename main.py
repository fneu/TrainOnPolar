import argparse
import configparser
import logging

import dateparser

from trainonpolar import trainasone

# read login details and default data from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# set up logging
logging.basicConfig()
logger = logging.getLogger("trainonpolar")
logger.setLevel(config["DEFAULT"]["log_level"])

# optional: read date from command line
argparser = argparse.ArgumentParser()
argparser.add_argument(
    'date',
    help='Date to import the workout for:\
        "tomorrow", "Wednesday", "2023-03-21" etc.',
    default=config["DEFAULT"]["default_date"],
    nargs="?")
args = argparser.parse_args()

date = (dateparser.parse(args.date, settings={'PREFER_DATES_FROM': 'future'}))
logger.debug(f'Parsed date "{args.date}" as "{date}"')

tao_session = trainasone.login(config)

