import argparse
import configparser

import dateparser

# read login details and default data from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

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

print(date)

