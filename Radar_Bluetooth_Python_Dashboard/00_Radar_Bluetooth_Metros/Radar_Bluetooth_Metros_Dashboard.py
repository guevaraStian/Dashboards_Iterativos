# En el siguiente codigo se muestra como lograr
# Obtener varios datos de los dispositivos bluetooth cercanos
# y como mostrar los datos en una pagina web
# pip install bleak flask


import asyncio
import threading
import time
from bleak import BleakScanner
from flask import Flask, jsonify, render_template

app = Flask(__name__)

devices_cache = []

TX_POWER = -59
PATH_LOSS_EXPONENT = 2.5

# En el siguiente codigo se calcula la distancia con la potencion RSSI
def Distancia_Estimada(rssi):
    if rssi == 0:
        return None
    return round(10 ** ((TX_POWER - rssi) / (10 * PATH_LOSS_EXPONENT)), 2)

# En el siguiente codigo se escanea los bluetooth cerca
async def Escaneo_Bluetooth():
    global devices_cache
    devices = await BleakScanner.discover(timeout=5)

    result = []
    for d in devices:
        result.append({
            "mac": d.address,
            "name": d.name or "Desconocido",
            "rssi": d.rssi,
            "distance": Distancia_Estimada(d.rssi)
        })

    devices_cache = result


def scanner_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        loop.run_until_complete(Escaneo_Bluetooth())
        time.sleep(10)

# Controladores de la pagina web del software
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/devices")
def api_devices():
    return jsonify(devices_cache)


if __name__ == "__main__":
    threading.Thread(target=scanner_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=True)
