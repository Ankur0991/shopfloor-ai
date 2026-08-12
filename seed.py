"""Seed ShopFloor IQ with machines and 30 days of backdated sensor readings.

Run from the project root:  python seed.py
Wipes existing machines and readings first, so it is safe to re-run.
"""

import random
from datetime import datetime, timedelta, timezone

from app import models
from app.database import SessionLocal, engine

random.seed(42)

DAYS = 30
READINGS_PER_DAY = 4

MACHINES = [
    {"name": "Symphoni-01", "line": "Assembly Line 2", "location": "Munich Hall 3"},
    {"name": "Symphoni-02", "line": "Assembly Line 2", "location": "Munich Hall 3"},
    {"name": "Palletiser-RX7", "line": "Packaging Line 1", "location": "Munich Hall 4"},
]

# metric: (start_value, end_value, unit, noise)
PROFILES = {
    "Symphoni-01": {
        "spindle_temp": (57.5, 58.4, "C", 0.8),
        "vibration_rms": (1.8, 2.0, "mm/s", 0.15),
        "cycle_time": (11.3, 11.5, "s", 0.2),
        "air_pressure": (6.2, 6.2, "bar", 0.05),
    },
    "Symphoni-02": {
        "spindle_temp": (58.1, 71.6, "C", 1.1),
        "vibration_rms": (1.9, 5.3, "mm/s", 0.25),
        "cycle_time": (11.4, 12.1, "s", 0.2),
        "air_pressure": (6.1, 6.1, "bar", 0.05),
    },
    "Palletiser-RX7": {
        "air_pressure": (6.3, 4.7, "bar", 0.08),
        "vibration_rms": (2.1, 2.3, "mm/s", 0.18),
        "cycle_time": (17.9, 18.9, "s", 0.35),
        "servo_current": (14.2, 14.8, "A", 0.4),
    },
}


def build_readings(machine_id, profile, now):
    total = DAYS * READINGS_PER_DAY
    step = timedelta(hours=24 / READINGS_PER_DAY)
    rows = []

    for metric, (start, end, unit, noise) in profile.items():
        for i in range(total):
            progress = i / (total - 1)
            value = start + (end - start) * progress + random.gauss(0, noise)
            rows.append(
                models.SensorReading(
                    machine_id=machine_id,
                    metric=metric,
                    value=round(value, 2),
                    unit=unit,
                    recorded_at=now - step * (total - 1 - i),
                )
            )
    return rows


def main():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    now = datetime.now(timezone.utc)

    try:
        db.query(models.SensorReading).delete()
        db.query(models.Machine).delete()
        db.commit()

        reading_count = 0
        for spec in MACHINES:
            machine = models.Machine(**spec, installed_at=now - timedelta(days=400))
            db.add(machine)
            db.flush()

            rows = build_readings(machine.id, PROFILES[machine.name], now)
            db.add_all(rows)
            reading_count += len(rows)

        db.commit()
        print(f"Seeded {len(MACHINES)} machines and {reading_count} readings.")
    finally:
        db.close()


if __name__ == "__main__":
    main()