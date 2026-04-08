"""
Flask API server for UAV Fleet Monitoring.
"""

import time
from datetime import datetime, timezone

from flask import Flask, jsonify, send_file, request
from prometheus_flask_exporter import PrometheusMetrics

from app.simulator import get_fleet, get_drone, get_fleet_summary, get_drone_history

app = Flask(__name__, static_folder=None)
metrics = PrometheusMetrics(app)

APP_START_TIME = time.time()


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/")
def index():
    return send_file("../frontend/index.html")


@app.route("/health")
def health():
    fleet = get_fleet()
    return jsonify({
        "status": "ok",
        "drone_count": len(fleet),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - APP_START_TIME, 2),
    })


@app.route("/drones")
def drones():
    return jsonify(get_fleet())


@app.route("/drones/<drone_id>/telemetry")
def drone_telemetry(drone_id: str):
    drone = get_drone(drone_id)
    if drone is None:
        return jsonify({"error": f"Drone '{drone_id}' not found", "path": request.path}), 404
    return jsonify(drone)


@app.route("/drones/<drone_id>/history")
def drone_history(drone_id: str):
    history = get_drone_history(drone_id)
    if history is None:
        return jsonify({"error": f"Drone '{drone_id}' not found", "path": request.path}), 404
    return jsonify(history)


@app.route("/fleet/summary")
def fleet_summary():
    return jsonify(get_fleet_summary())


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found", "path": request.path}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
