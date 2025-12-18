from flask import Flask, jsonify, render_template, send_file
from network_scanner import scan_network
from exporter import export_excel, export_pdf
from datetime import datetime
import requests
app = Flask(__name__)

known_devices = set()

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/devices")
def api_devices():
    global known_devices
    devices = scan_network()

    current = set(d["mac"] for d in devices)
    new = list(current - known_devices)
    known_devices = current

    return jsonify({
        "devices": devices,
        "new_devices": new
    })

@app.route("/download/excel")
def download_excel():
    return send_file(export_excel(), as_attachment=True)

@app.route("/download/pdf")
def download_pdf():
    return send_file(export_pdf(), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
