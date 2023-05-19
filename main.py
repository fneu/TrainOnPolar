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

tao_session = trainasone.login(config)

