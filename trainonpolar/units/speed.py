from abc import ABC, abstractmethod


class Speed(ABC):
    @abstractmethod
    def as_mps(self):
        pass

    def as_kph(self):
        return self.as_mps() * 3.6

    def as_pace(self):
        """
        Converts meters per second to a pace per kilometer string
        in the format of M:SS
        """
        mps = self.as_mps()
        return f"{int(1000 / mps // 60)}:{int(1000 / mps % 60 + 0.5):02d}"

    def __sub__(self, other):
        return MPS(self.as_mps() - other.as_mps())

    def __add__(self, other):
        return MPS(self.as_mps() + other.as_mps())


class MPS(Speed):
    def __init__(self, mps):
        self._mps = mps

    def as_mps(self):
        return self._mps


class KPH(Speed):
    def __init__(self, kph):
        self._kph = kph

    def as_mps(self):
        return self._kph / 3.6


class Pace(Speed):
    def __init__(self, pace):
        self._pace = pace

    def as_mps(self):
        minutes, seconds = self._pace.split(":")
        return 1000 / (int(minutes) * 60 + int(seconds))
