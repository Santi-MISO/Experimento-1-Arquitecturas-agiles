import requests, time
from flask import Flask, jsonify
from threading import Thread, Event

app = Flask(__name__)


HEARTBEAT_INTERVAL_S = 1.0
TARGET = "http://clientes:5001/health"
stop_event = Event()

status = {"service": "unknown", "last_checked_ns": None}

def now_ns():
    return time.time_ns()

def write_monitor_log(line: str):
    with open("report_monitor.txt", "a") as f:
        f.write(line + "\n")

def heartbeat_loop():
    last_status = None

    while not stop_event.is_set():
        
        ts = now_ns()

        try:
            r = requests.get(TARGET, timeout=0.9)
            status["last_checked_ns"] = ts
            if r.status_code == 200:
                curr = "up"
                if curr != last_status:
                    write_monitor_log(f"{ts},UP,")
                    last_status = curr
            else:
                curr = "down"
                fail_ts_ns = None
                try:
                    fail_ts_ns = r.json().get("fail_ts_ns", None)
                except Exception:
                    pass
                if curr != last_status:
                    if fail_ts_ns:
                        latency_ms = max(10.0, (ts - int(fail_ts_ns)) / 1_000_000.0)
                        write_monitor_log(f"{ts},DOWN,latency_ms={latency_ms:.3f}")
                    else:
                        write_monitor_log(f"{ts},DOWN,latency_ms=NA")
                    last_status = curr
        except Exception:
            status["last_checked_ns"] = ts
            curr = "down"
            if curr != last_status:
                write_monitor_log(f"{ts},DOWN,latency_ms=NA")
                last_status = curr
        finally:
            stop_event.wait(HEARTBEAT_INTERVAL_S)

@app.route("/estado_clientes")
def estado():
    return jsonify(status)

if __name__ == "__main__":
    with open("report_monitor.txt", "w") as f:
        f.write("ts_ns,event,extra\n")
        f.write(f"{now_ns()},START,\n")
    t = Thread(target=heartbeat_loop, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5002)
    stop_event.set()