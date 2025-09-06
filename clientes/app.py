from flask import Flask, jsonify
from threading import Thread, Event
import time, random

app = Flask(__name__)

# Estados de la aplicación
STATE_UP = "up"
STATE_DOWN = "down"

state = {"status": STATE_UP, "fail_ts_ns": None}
stop_event = Event()

# Configuración del generador de fallos
MEAN_SECONDS_BETWEEN_FAILURES = 3.0
# Duración del fallo aleatorio de 1 a 2 segundos
FAIL_DURATION_RANGE = (1.0, 2.0)

def now_ns():
    return time.time_ns()  # epoch ns: comparable entre procesos del mismo host

# Generación del fallo con captura del tiempo del fallo
def failure_generator():
    while not stop_event.is_set():
        # Espera hasta el próximo fallo
        wait_s = random.expovariate(1.0 / MEAN_SECONDS_BETWEEN_FAILURES) # Calculo del tiempo hasta la siguiente falla
        stop_event.wait(wait_s)
        if stop_event.is_set():
            break

        # Entra en DOWN
        state["status"] = STATE_DOWN
        state["fail_ts_ns"] = now_ns()

        # Mantiene el fallo por el tiempo aleatorio definido previamente
        down_seconds = random.uniform(*FAIL_DURATION_RANGE)
        stop_event.wait(down_seconds)
        if stop_event.is_set():
            break

        # Vuelve a UP
        state["status"] = STATE_UP
        state["fail_ts_ns"] = None

@app.route("/health")
def health():
    if state["status"] == STATE_UP:
        return jsonify({"status": "ok"}), 200
    # Incluye el timestamp de inicio de fallo para que el monitor calcule latencia exacta
    return jsonify({"status": "error", "fail_ts_ns": state["fail_ts_ns"]}), 500

# Simulación de retorno de la logica de negocio
@app.route("/clientes")
def get_clientes():
    return jsonify([
        {"id": 1, "nombre": "Carlos"},
        {"id": 2, "nombre": "Nicolas"},
        {"id": 3, "nombre": "Santiago"}
    ])

if __name__ == "__main__":
    t = Thread(target=failure_generator, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5001)
    stop_event.set()