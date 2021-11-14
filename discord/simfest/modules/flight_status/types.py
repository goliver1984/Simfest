from typing import Optional, TypedDict


class FlightPayload(TypedDict):
    UniqueId: int
    FlightNumber: str
    Sta: str
    Std: str
    Remarks: Optional[str]
    Departure: str
    DeptIcao: str
    Destination: str
    ArrIcao: str
