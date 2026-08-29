"""Seed ShopFloor IQ with a user, machines, and 30 days of backdated sensor readings.

Run from the project root:  python seed.py
Wipes existing users, machines, and readings first, so it is safe to re-run.
"""

import random
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from app import models
from app.database import SessionLocal, engine
from app.utils import hash_password
from sqlalchemy import text

random.seed(42)  # reproducible values across runs, for screenshots and evaluation

DAYS = 30
READINGS_PER_DAY = 4
READINGS_PER_METRIC = DAYS * READINGS_PER_DAY
INTERVAL = timedelta(hours=24 / READINGS_PER_DAY)

SEED_USER = {
    "email": "seed@shopfloor.ai",
    "password": "seedpassword123",
    "full_name": "Seed User",
}

MACHINES = [
    {"name": "Symphoni-01", "line": "Assembly Line 2", "location": "Munich Hall 3"},
    {"name": "Symphoni-02", "line": "Assembly Line 2", "location": "Munich Hall 3"},
    {"name": "Palletiser-RX7", "line": "Packaging Line 1", "location": "Munich Hall 4"},
]


class MetricProfile(NamedTuple):
    """A metric's linear drift from `start` to `end` across the whole window."""

    start: float
    end: float
    unit: str
    noise: float  # stddev of the gaussian jitter added to each point


# Symphoni-01 is the healthy baseline. Symphoni-02 has bearing degradation:
# vibration and spindle temp rise together, which is the real diagnostic pattern.
# Palletiser-RX7 has pneumatic decay: air pressure falls, everything else flat.
PROFILES = {
    "Symphoni-01": {
        "spindle_temp": MetricProfile(57.5, 58.4, "C", 0.8),
        "vibration_rms": MetricProfile(1.8, 2.0, "mm/s", 0.15),
        "cycle_time": MetricProfile(11.3, 11.5, "s", 0.2),
        "air_pressure": MetricProfile(6.2, 6.2, "bar", 0.05),
    },
    "Symphoni-02": {
        "spindle_temp": MetricProfile(58.1, 71.6, "C", 1.1),
        "vibration_rms": MetricProfile(1.9, 5.3, "mm/s", 0.25),
        "cycle_time": MetricProfile(11.4, 12.1, "s", 0.2),
        "air_pressure": MetricProfile(6.1, 6.1, "bar", 0.05),
    },
    "Palletiser-RX7": {
        "air_pressure": MetricProfile(6.3, 4.7, "bar", 0.08),
        "vibration_rms": MetricProfile(2.1, 2.3, "mm/s", 0.18),
        "cycle_time": MetricProfile(17.9, 18.9, "s", 0.35),
        "servo_current": MetricProfile(14.2, 14.8, "A", 0.4),
    },
}


def build_readings(machine_id, profiles, latest_at, created_by):
    """One SensorReading per metric per interval, oldest first, ending at `latest_at`.

    `recorded_at` is set explicitly rather than left to the column's server_default,
    which only fires when the column is omitted from the INSERT. Setting it is what
    lets the history be backdated.
    """
    readings = []

    for metric, profile in profiles.items():
        for i in range(READINGS_PER_METRIC):
            # 0.0 at the oldest reading, 1.0 at the newest
            progress = i / (READINGS_PER_METRIC - 1) if READINGS_PER_METRIC > 1 else 1.0
            drift = profile.start + (profile.end - profile.start) * progress
            age = INTERVAL * (READINGS_PER_METRIC - 1 - i)

            readings.append(
                models.SensorReading(
                    machine_id=machine_id,
                    metric=metric,
                    value=round(drift + random.gauss(0, profile.noise), 2),
                    unit=profile.unit,
                    recorded_at=latest_at - age,
                    created_by=created_by,
                )
            )

    return readings


def wipe(db):
    """TRUNCATE resets identity sequences; DELETE does not.

    Without RESTART IDENTITY the seeded ids climb on every re-run, which breaks
    any test, screenshot, or doc that refers to a machine by id.
    """
    db.execute(
        text("TRUNCATE sensor_readings, machines, users RESTART IDENTITY CASCADE")
    )
    db.commit()

def main():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    latest_at = datetime.now(timezone.utc)

    try:
        wipe(db)

        user = models.User(
            email=SEED_USER["email"],
            hashed_password=hash_password(SEED_USER["password"]),
            full_name=SEED_USER["full_name"],
        )
        db.add(user)
        db.flush()  # assigns user.id without committing

        reading_count = 0
        for machine_spec in MACHINES:
            machine = models.Machine(
                **machine_spec,
                installed_at=latest_at - timedelta(days=400),
                created_by=user.id,
            )
            db.add(machine)
            db.flush()  # assigns machine.id, needed as the readings' foreign key

            readings = build_readings(
                machine_id=machine.id,
                profiles=PROFILES[machine.name],
                latest_at=latest_at,
                created_by=user.id,
            )
            db.add_all(readings)
            reading_count += len(readings)

        db.commit()
        print(f"Seeded 1 user, {len(MACHINES)} machines, {reading_count} readings.")
        print(f"Login: {SEED_USER['email']} / {SEED_USER['password']}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()