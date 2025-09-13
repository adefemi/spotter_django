from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Literal

DutyStatus = Literal["OFF", "SB", "D", "ON"]


@dataclass
class DutySegment:
    start: datetime
    end: datetime
    status: DutyStatus
    note: str = ""

#This is the Hours of Service class that will be used to plan the trip.
class HOSPlanner:
    def __init__(self, start_time: datetime, cycle_hours_used: float) -> None:
        self.current_time = start_time
        self.driving_in_window = 0.0
        self.driving_since_last_break = 0.0
        self.on_duty_window = 0.0
        self.cycle_hours_used = cycle_hours_used
        self.segments: List[DutySegment] = []

    def _add_segment(self, duration_hours: float, status: DutyStatus, note: str = "") -> None:
        start = self.current_time
        end = start + timedelta(hours=duration_hours)
        self.segments.append(DutySegment(start=start, end=end, status=status, note=note))
        self.current_time = end
        if status in ("D", "ON"):
            self.on_duty_window += duration_hours
            self.cycle_hours_used += duration_hours
        if status == "D":
            self.driving_in_window += duration_hours
            self.driving_since_last_break += duration_hours

    def _reset_day(self) -> None:
        self.driving_in_window = 0.0
        self.driving_since_last_break = 0.0
        self.on_duty_window = 0.0

    def ensure_break_if_needed(self) -> None:
        if self.driving_since_last_break >= 8.0:
            self._add_segment(0.5, "OFF", note="30-min break")
            # break resets the 8-hour driving clock, not 11/14
            self.driving_since_last_break = 0.0

    def ensure_rest_if_needed(self) -> None:
        if self.driving_in_window >= 11.0 or self.on_duty_window >= 14.0:
            self._add_segment(10.0, "OFF", note="10-hr rest")
            self._reset_day()

    def ensure_cycle_if_needed(self) -> None:
        if self.cycle_hours_used >= 70.0:
            self._add_segment(34.0, "OFF", note="34-hr restart")
            self.cycle_hours_used = 0.0
            self._reset_day()

    def add_pickup(self) -> None:
        self._add_segment(1.0, "ON", note="Pickup loading")

    def add_dropoff(self) -> None:
        self._add_segment(1.0, "ON", note="Dropoff unloading")

    def drive(self, drive_hours: float) -> None:
        remaining_drive = drive_hours
        while remaining_drive > 0:
            # enforce break and clocks
            self.ensure_break_if_needed()
            self.ensure_rest_if_needed()
            self.ensure_cycle_if_needed()

            # max drive available now before hitting 11/14
            drive_cap = min(11.0 - self.driving_in_window, 14.0 - self.on_duty_window)
            if drive_cap <= 0:
                # must rest
                self._add_segment(10.0, "OFF", note="10-hr rest")
                self._reset_day()
                continue

            # also cap to before next required 30-min break
            break_cap = 8.0 - self.driving_since_last_break
            if break_cap <= 0:
                # need break now
                self.ensure_break_if_needed()
                continue

            this_leg = min(remaining_drive, drive_cap, break_cap)
            self._add_segment(this_leg, "D", note="Driving")
            remaining_drive -= this_leg

    def add_fuel_stop(self) -> None:
        # Treat fueling as on-duty not driving
        self._add_segment(0.5, "ON", note="Fueling")


