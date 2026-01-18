# pip install bleak flask
# Python 3.13

import asyncio
import threading
import time
import math
from bleak import BleakScanner
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

devices_cache = []

TX_POWER = -59
PATH_LOSS_EXPONENT = 2.5
EARTH_RADIUS = 6378137  # metros

# Coordenadas del dispositivo creador
creator_position = {
    "lat": None,
    "lon": None
}

# Se calcula el RSSI de cada dispositivo bluetooth encendidos
def Distancia_Estimada(rssi):
    if rssi == 0:
        return None
    return round(10 ** ((TX_POWER - rssi) / (10 * PATH_LOSS_EXPONENT)), 2)

# Usando el RSSI y la direccion, se calculas las coordenadas de el bluetooth encendido
def calcular_coordenadas(lat, lon, distancia, angulo):
    ang_rad = math.radians(angulo)
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)

    lat2 = lat1 + (distancia / EARTH_RADIUS) * math.cos(ang_rad)
    lon2 = lon1 + (distancia / EARTH_RADIUS) * math.sin(ang_rad) / math.cos(lat1)

    return round(math.degrees(lat2), 6), round(math.degrees(lon2), 6)

# Se inicia el escaneo de los bluetooth
async def Escaneo_Bluetooth():
    global devices_cache

    devices = await BleakScanner.discover(timeout=5)
    total = len(devices)
    result = []

    for i, d in enumerate(devices):
        distancia = Distancia_Estimada(d.rssi)
        angulo = (360 / total) * i if total > 0 else 0

        lat, lon = None, None
        if creator_position["lat"] is not None and distancia:
            lat, lon = calcular_coordenadas(
                creator_position["lat"],
                creator_position["lon"],
                distancia,
                angulo
            )

        result.append({
            "mac": d.address,
            "name": d.name or "Desconocido",
            "rssi": d.rssi,
            "distance": distancia,
            "lat": lat,
            "lon": lon,
            "angle": round(angulo, 1)
        })

    devices_cache = result

# Se carga el escaneo de lo bluetooths
def scanner_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while True:
        loop.run_until_complete(Escaneo_Bluetooth())
        time.sleep(10)

# Se crea la pagina con flask
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        creator_position["lat"] = float(request.form["lat"])
        creator_position["lon"] = float(request.form["lon"])
    return render_template("index.html", creator=creator_position)

@app.route("/api/devices")
def api_devices():
    return jsonify(devices_cache)

# Se correo el main de ejecucion
if __name__ == "__main__":
    threading.Thread(target=scanner_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=True)
