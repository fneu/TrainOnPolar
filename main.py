import configparser
import logging


from trainonpolar import trainasone, polarflow, cache, zonecalc

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

zones_lower_bounds = zonecalc.lower_kph_bounds(workout)
polarflow.set_zones(flow_session, config, zones_lower_bounds)

phased_target = polarflow.phased_target_from_garmin(workout, next_run_date, zones_lower_bounds)

conflicting_target = polarflow.check_conflicting_target(flow_session, next_run_date)
if conflicting_target:
    if cache.is_last_uploaded(conflicting_target):
        if cache.tao_unchanged(phased_target):
            logger.warning("Did NOT upload phased target. "
                           "Last uploaded target still exists in polar flow "
                           "and the TAO workout didn't change since: "
                           f"https://flow.polar.com/target/{conflicting_target}\n"
                           "If you changed the phased target in flow, "
                           "please delete it manually.")
            exit(1)
        elif config.getboolean("polarflow", "allow_deletion_of_training_targets"):
            polarflow.delete(flow_session, conflicting_target)
        else:
            logger.error("The previously uploaded target exists in flow,\n"
                         "but the TrainAsOne Workout has changed.\n"
                         "Please delete "
                         f"https://flow.polar.com/target/{conflicting_target} "
                         "manually, or allow auto-deletion in config.ini")
            exit(1)
    else:
        logger.error("A unknown conflicting target exists in flow.\n"
                     "Please delete "
                     f"https://flow.polar.com/target/{conflicting_target} "
                     "manually")
        exit(1)

id = polarflow.upload(flow_session, phased_target)
if id:
    cache.save(phased_target, id)
