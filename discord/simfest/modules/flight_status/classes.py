from datetime import datetime, timedelta
from typing import Optional

from discord import Embed, Colour

from .enums import FlightStatus
from .types import FlightPayload


class Airport(object):
    def __init__(self, icao: str, name: str) -> None:
        self.icao = icao
        self.name = name

    def __str__(self) -> str:
        return f"{self.name} ({self.icao})"


class Flight(object):
    def __init__(self, data: FlightPayload) -> None:
        self.id = data["UniqueId"]
        self.flight_number = data["FlightNumber"]

        tmp = datetime.strptime(data["Std"], "%H%M")
        self.etd = datetime.utcnow().replace(hour=tmp.hour, minute=tmp.minute)
        # If the ETD is more than 12 hours in the future assume it's
        # because we're updating this after midnight and the ETD
        # was actually before midnight.
        if self.etd - timedelta(hours=12) > datetime.utcnow():
            self.etd -= timedelta(days=1)

        tmp = datetime.strptime(data["Sta"], "%H%M")
        self.eta = self.etd.replace(hour=tmp.hour, minute=tmp.minute)
        if self.eta < self.etd:
            self.eta += timedelta(days=1)

        self.remarks = data["Remarks"]
        self.departure = Airport(data["DeptIcao"], data["Departure"])
        self.destination = Airport(data["ArrIcao"], data["Destination"])

        self._needs_posting = False
        self._last_status = self.status
        self._last_rmk_posted = None
        self._last_rmk_update = datetime.utcnow()

    @property
    def status(self) -> Optional[FlightStatus]:
        status = None
        if self._is_departing():
            status = FlightStatus.DEPARTING
        elif self._is_boarding():
            status = FlightStatus.BOARDING
        elif self._is_cruising():
            status = FlightStatus.CRUISING
        elif self._is_arrived():
            status = FlightStatus.ARRIVED
        return status

    def _is_departing(self) -> bool:
        return self.remarks and any(
            self.remarks.startswith(s) for s in ("Taxi", "Departed", "Gate Closed")
        )

    def _is_boarding(self) -> bool:
        return self.remarks and self.remarks.startswith("Boarding")

    def _is_cruising(self) -> bool:
        return self.remarks and self.remarks.startswith("Expected")

    def _is_arrived(self) -> bool:
        return self.remarks and any(
            self.remarks.startswith(s) for s in ("Landed", "Arrived")
        )

    def _has_stable_eta(self) -> bool:
        return (
            self.status is FlightStatus.CRUISING and
            self._last_rmk_update <= datetime.utcnow() - timedelta(minutes=15)
        )

    def get_embed(self) -> Embed:
        embed = Embed(
            title=f"Flight #{self.flight_number}",
            colour=Colour.from_rgb(155, 89, 182)
        )

        embed.add_field(name="From", value=f"{self.departure}", inline=True)
        embed.add_field(name="To", value=f"{self.destination}", inline=True)

        description = None
        name, timestamp = None, None

        status = self.status
        if status is FlightStatus.DEPARTING:
            description = "🛫 Departing 🛫"
            name, timestamp = "ETA (Planned)", self.eta.timestamp()
        elif status is FlightStatus.BOARDING:
            description = "📣 Boarding 📣"
            name, timestamp = "ETD", self.etd.timestamp()
        elif status is FlightStatus.CRUISING:
            description = "☁️ Enroute ☁️"
            name, timestamp = "ETA (Expected)", self.get_remarks_datetime().timestamp()
        elif status is FlightStatus.ARRIVED:
            embed.description = "✅ Arrived ✅"
            name, timestamp = "ATA", self.get_remarks_datetime().timestamp()

        if description is not None:
            embed.description = description

        if name is not None and timestamp is not None:
            timestamp = int(timestamp)
            embed.add_field(
                name=name,
                value=f"<t:{timestamp}:f> (<t:{timestamp}:R>)",
                inline=False
            )

        return embed

    def get_remarks_datetime(self) -> Optional[datetime]:
        if self.status in (FlightStatus.CRUISING, FlightStatus.ARRIVED):
            rmks = self.remarks[-5:]
            tmp = datetime.strptime(rmks, "%H:%M")
            rmk_eta = self.etd.replace(hour=tmp.hour, minute=tmp.minute)
            if rmk_eta < self.etd:
                rmk_eta += timedelta(days=1)
            return rmk_eta

    def mark_posted(self) -> None:
        self._needs_posting = False
        self._last_rmk_posted = self.remarks

    def needs_posting(self) -> bool:
        if self.status is FlightStatus.CRUISING:
            return self._needs_posting and self._has_stable_eta()
        return self._needs_posting

    def update(self, data: FlightPayload) -> None:
        status = self.status
        if self.remarks != data["Remarks"]:
            self.remarks = data["Remarks"]
            self._last_rmk_update = datetime.utcnow()
            if (
                (
                    self.status is FlightStatus.CRUISING and
                    self.remarks != self._last_rmk_posted
                )
                or self.status != status
            ):
                self._needs_posting = True

        tmp = datetime.strptime(data["Std"], "%H%M")
        self.etd = datetime.utcnow().replace(hour=tmp.hour, minute=tmp.minute)
        # If the ETD is more than 12 hours in the future assume it's
        # because we're updating this after midnight and the ETD
        # was actually before midnight.
        if self.etd - timedelta(hours=12) > datetime.utcnow():
            self.etd -= timedelta(days=1)

        tmp = datetime.strptime(data["Sta"], "%H%M")
        self.eta = self.etd.replace(hour=tmp.hour, minute=tmp.minute)
        if self.eta < self.etd:
            self.eta += timedelta(days=1)
