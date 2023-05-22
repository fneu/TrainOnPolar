import logging

from typing import List
from trainonpolar.units.speed import Speed, MPS

logger = logging.getLogger(__name__)


class Zone():
    def __init__(self, min: Speed, max: Speed, config: any):
        self.min = min
        self.max = max

        if config:
            assert (((self.max - self.min).as_mps() + 0.0001)
                    >= 2 * float(config["zones"]["min_zone_radius_mps"])), \
                    "Zone is smaller than 2 * minimum zone radius."

    @classmethod
    def around(cls, speed: Speed, config: any):
        return cls(speed - MPS(float(config["zones"]["min_zone_radius_mps"])),
                   speed + MPS(float(config["zones"]["min_zone_radius_mps"])),
                   config)

    @classmethod
    def between(cls, below: 'Zone', above: 'Zone', config: any):
        return cls(below.max, above.min, config)

    @classmethod
    def inside_overlap(cls, below: 'Zone', above: 'Zone'):
        return cls(above.min,
                   below.max,
                   {"zones": {"min_zone_radius_mps": 0.0}})

    @classmethod
    def beyond(cls, below: 'Zone', config: any):
        return cls(below.max,
                   below.max + MPS(2 * float(config["zones"]["min_zone_radius_mps"])),
                   config)

    @classmethod
    def across(cls, below: 'Zone', above: 'Zone', config: any):
        return cls(below.min, above.max, config)

    def retreat(self, other: 'Zone'):
        if self.min.as_mps() < other.min.as_mps():
            self.max = other.min
        elif self.max.as_mps() > other.max.as_mps():
            self.min = other.max
        else:
            raise Exception("Zone cannot retreat, other zone encloses it")

    def meet(self, other: Speed):
        center = (self.min.as_mps() + self.max.as_mps()) / 2
        if other.as_mps() <= center:
            self.min = other
        else:
            self.max = other

    def __repr__(self):
        return f"Zone({self.min.as_pace()}, {self.max.as_pace()})"

    def __eq__(self, other):
        return (self.min.as_mps() == other.min.as_mps()
                and self.max.as_mps() == other.max.as_mps())


def calc_zones(speeds: List[Speed], config):
    zones = [Zone.around(speed, config) for speed in speeds]
    zones.sort(key=lambda zone: zone.min.as_mps())

    # remove duplicates. TODO: Make zone hashable and use set
    unique_zones = []
    for zone in zones:
        if (not unique_zones) or (zone != unique_zones[-1]):
            unique_zones.append(zone)

    logger.debug(f"initial zones: {unique_zones}")

    # number of overlaps
    overlaps = 0
    for i in range(len(unique_zones) - 1):
        if unique_zones[i].max.as_mps() > (unique_zones[i + 1].min.as_mps() + 0.01):
            overlaps += 1

    logger.debug(f"Overlaps: {overlaps}")

    # overlap the two zones which are closest together
    # as long as we have too many (overlapping) zones
    # overlaps will be new zones soon
    while (len(unique_zones) + overlaps) > 5:
        min_range = float("inf")
        min_range_index = None
        for i in range(len(unique_zones) - 1):
            r = (unique_zones[i + 1].max.as_mps()
                 - unique_zones[i].min.as_mps())
            if r < min_range:
                min_range = r
                min_range_index = i
        unique_zones = (unique_zones[:min_range_index]
                        + [Zone.across(unique_zones[min_range_index],
                                       unique_zones[min_range_index + 1],
                                       config)]
                        + unique_zones[min_range_index + 2:])
        overlaps = 0  # might have changed
        for i in range(len(unique_zones) - 1):
            if unique_zones[i].max.as_mps() > (unique_zones[i + 1].min.as_mps() + 0.01):
                overlaps += 1

    logger.debug(f"zones after merge: {unique_zones}")

    # create new zones from overlaps
    while overlaps > 0:
        max_overlap = 0
        max_overlap_index = None
        for i in range(len(unique_zones) - 1):
            overlap = (unique_zones[i].max.as_mps()
                       - unique_zones[i+1].min.as_mps())
            if overlap > max_overlap:
                max_overlap = overlap
                max_overlap_index = i
        new_zone = Zone.inside_overlap(unique_zones[max_overlap_index],
                                       unique_zones[max_overlap_index+1])
        unique_zones[max_overlap_index].retreat(new_zone)
        unique_zones[max_overlap_index+1].retreat(new_zone)
        unique_zones = (unique_zones[:max_overlap_index+1]
                        + [new_zone]
                        + unique_zones[max_overlap_index + 1:])
        overlaps -= 1

    logger.debug(f"zones after overlaps: {unique_zones}")

    # if we ended up (or started) with less than 5 zones,
    # try to shift some in gaps:
    gap_fillers = []
    for i in range(len(unique_zones) - 1):
        try:
            between_zone = Zone.between(unique_zones[i],
                                        unique_zones[i+1],
                                        config)
            gap_fillers.append(between_zone)
        except AssertionError:
            pass
    gap_fillers.sort(key=lambda x: x.max.as_mps() - x.min.as_mps())

    while len(unique_zones) < 5 and len(gap_fillers) > 0:
        unique_zones.append(gap_fillers.pop(0))
        unique_zones.sort(key=lambda x: x.min.as_mps())

    logger.debug(f"zones after gap fillers: {unique_zones}")

    # if we still have less than 5 zones,
    # just put them on top
    while len(unique_zones) < 5:
        unique_zones.append(Zone.beyond(unique_zones[-1], config))

    logger.debug(f"zones after top fillers: {unique_zones}")

    # make sure all zones are adjacent
    for i in range(len(unique_zones) - 1):
        if unique_zones[i].max.as_mps() != unique_zones[i + 1].min.as_mps():
            center = MPS((unique_zones[i].max.as_mps()
                          + unique_zones[i + 1].min.as_mps()) / 2)
            unique_zones[i].meet(center)
            unique_zones[i+1].meet(center)

    logger.debug(f"zones after meeting: {unique_zones}")

    return unique_zones
