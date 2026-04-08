"""
UAV Drone Fleet Simulation Engine.
Maintains live state for 5 drones, ticking on each read.
"""

import random
import math
import time
from datetime import datetime, timezone
from threading import Lock

_lock = Lock()

BASE_LAT = 37.4
BASE_LON = -122.1

MISSIONS = ["SURVEILLANCE", "DELIVERY", "MAPPING", "PATROL"]

_fleet: dict = {}


def _make_drone(drone_id: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    lat = random.uniform(37.3850, 37.4150)
    lon = random.uniform(-122.1500, -122.0500)
    return {
        "id": drone_id,
        "lat": lat,
        "lon": lon,
        "battery": random.uniform(70.0, 100.0),
        "altitude": random.uniform(80.0, 180.0),
        "speed": random.uniform(15.0, 45.0),
        "heading": random.uniform(0, 359),
        "mission": random.choice(MISSIONS),
        "status": "ACTIVE",
        "last_status_change": now,
        "flight_time_seconds": 0,
        "distance_traveled_km": 0.0,
        "position_history": [(lat, lon)],
    }


def _init_fleet() -> None:
    for i in range(1, 6):
        drone_id = f"UAV-{i:03d}"
        _fleet[drone_id] = _make_drone(drone_id)


def _compute_status(battery: float) -> str:
    if battery >= 35.0:
        return "ACTIVE"
    if battery >= 20.0:
        return "RETURNING"
    if battery >= 10.0:
        return "LOW_BATTERY"
    return "OFFLINE"


def _compute_signal(lat: float, lon: float) -> float:
    dist = math.sqrt((lat - BASE_LAT) ** 2 + (lon - BASE_LON) ** 2)
    max_dist = math.sqrt(0.03 ** 2 + 0.05 ** 2) * 3.0
    raw = max(0.0, 1.0 - dist / max_dist) * 100.0
    noise = random.uniform(-5, 5)
    return max(0.0, min(100.0, raw + noise))


def _compute_threat(status: str, signal: float) -> str:
    if status == "OFFLINE":
        return "UNKNOWN"
    if status == "LOW_BATTERY" or signal < 40:
        return "CRITICAL"
    if status == "RETURNING" or signal <= 70:
        return "ELEVATED"
    return "NOMINAL"


def _tick_drone(drone: dict) -> dict:
    now_iso = datetime.now(timezone.utc).isoformat()

    drone["lat"] += random.uniform(-0.0003, 0.0003)
    drone["lon"] += random.uniform(-0.0003, 0.0003)

    drone["battery"] = max(0.0, drone["battery"] - random.uniform(0.05, 0.25))
    drone["altitude"] = max(10.0, min(250.0, drone["altitude"] + random.uniform(-8, 8)))
    drone["speed"] = max(0.0, min(80.0, drone["speed"] + random.uniform(-3, 3)))

    new_heading = drone["heading"] + random.uniform(-8, 8)
    if new_heading >= 360:
        new_heading -= 360
    elif new_heading < 0:
        new_heading += 360
    drone["heading"] = new_heading

    drone["flight_time_seconds"] += 2
    drone["distance_traveled_km"] += drone["speed"] / 1800.0

    history = drone["position_history"]
    history.append((drone["lat"], drone["lon"]))
    if len(history) > 20:
        history = history[-20:]
    drone["position_history"] = history

    new_status = _compute_status(drone["battery"])
    if new_status != drone["status"]:
        drone["status"] = new_status
        drone["last_status_change"] = now_iso

    drone["signal_strength"] = _compute_signal(drone["lat"], drone["lon"])
    drone["threat_level"] = _compute_threat(drone["status"], drone["signal_strength"])

    return drone


def _drone_to_dict(drone: dict) -> dict:
    return {
        "id": drone["id"],
        "lat": drone["lat"],
        "lon": drone["lon"],
        "battery": round(drone["battery"], 2),
        "altitude": round(drone["altitude"], 1),
        "speed": round(drone["speed"], 1),
        "heading": round(drone["heading"], 1),
        "status": drone["status"],
        "mission": drone["mission"],
        "signal_strength": round(drone["signal_strength"], 1),
        "threat_level": drone["threat_level"],
        "last_status_change": drone["last_status_change"],
        "flight_time_seconds": drone["flight_time_seconds"],
        "distance_traveled_km": round(drone["distance_traveled_km"], 3),
    }


_init_fleet()


def get_fleet() -> list:
    with _lock:
        result = []
        for drone in _fleet.values():
            _tick_drone(drone)
            result.append(_drone_to_dict(drone))
        return result


def get_drone(drone_id: str):
    with _lock:
        drone = _fleet.get(drone_id)
        if drone is None:
            return None
        _tick_drone(drone)
        return _drone_to_dict(drone)


def get_fleet_summary() -> dict:
    with _lock:
        drones = [_drone_to_dict(d) for d in _fleet.values()]

    statuses = [d["status"] for d in drones]
    active = statuses.count("ACTIVE")
    returning = statuses.count("RETURNING")
    low_battery = statuses.count("LOW_BATTERY")
    offline = statuses.count("OFFLINE")
    total = len(drones)

    batteries = [d["battery"] for d in drones]
    altitudes = [d["altitude"] for d in drones]
    speeds = [d["speed"] for d in drones]
    total_dist = sum(d["distance_traveled_km"] for d in drones)

    avg_battery = sum(batteries) / total if total else 0.0
    avg_altitude = sum(altitudes) / total if total else 0.0
    avg_speed = sum(speeds) / total if total else 0.0

    threats = [d["threat_level"] for d in drones]
    if "CRITICAL" in threats:
        fleet_threat = "CRITICAL"
    elif "ELEVATED" in threats:
        fleet_threat = "ELEVATED"
    elif "UNKNOWN" in threats:
        fleet_threat = "ELEVATED"
    else:
        fleet_threat = "NOMINAL"

    return {
        "total": total,
        "active": active,
        "returning": returning,
        "low_battery": low_battery,
        "offline": offline,
        "avg_battery": round(avg_battery, 2),
        "avg_altitude": round(avg_altitude, 1),
        "avg_speed": round(avg_speed, 1),
        "total_distance_km": round(total_dist, 3),
        "fleet_threat_level": fleet_threat,
    }


def get_drone_history(drone_id: str):
    with _lock:
        drone = _fleet.get(drone_id)
        if drone is None:
            return None
        return list(drone["position_history"])


def recharge_drone(drone_id: str):
    with _lock:
        drone = _fleet.get(drone_id)
        if drone is None:
            return None
        drone["battery"] = 100.0
        drone["status"] = "ACTIVE"
        drone["last_status_change"] = datetime.now(timezone.utc).isoformat()
        _tick_drone(drone)
        return _drone_to_dict(drone)
