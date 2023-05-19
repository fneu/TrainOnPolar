import configparser
import logging


from trainonpolar import trainasone, polarflow

# read login details and default data from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# set up logging
logging.basicConfig()
logger = logging.getLogger("trainonpolar")
logger.setLevel(config["DEFAULT"]["log_level"])

tao_session = trainasone.login(config)
flow_session = polarflow.login(config)

next_run_url, next_run_date = trainasone.next_run(tao_session)
workout = trainasone.get_workout(tao_session, next_run_url)

phased_target = polarflow.phased_target_from_garmin(workout, next_run_date)
polarflow.upload(flow_session, phased_target)
