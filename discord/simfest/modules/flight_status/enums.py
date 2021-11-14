from enum import auto, Enum


class FlightStatus(Enum):
    BOARDING = auto()
    DEPARTING = auto()
    CRUISING = auto()
    ARRIVED = auto()
