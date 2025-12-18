import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from network_scanner import scan_network

EXCEL_PATH = "exports/devices.xlsx"
PDF_PATH = "exports/dashboard.pdf"

def export_excel():
    devices = scan_network()
    df = pd.DataFrame(devices)
    df.to_excel(EXCEL_PATH, index=False)
    return EXCEL_PATH

def export_pdf():
    devices = scan_network()

    c = canvas.Canvas(PDF_PATH, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 40, "Dashboard WiFi - Dispositivos Conectados")

    c.setFont("Helvetica", 9)
    y = height - 80

    headers = ["IP", "MAC", "Nombre", "Zona", "Distancia (m)"]
    x_positions = [40, 130, 270, 420, 480]

    for i, h in enumerate(headers):
        c.drawString(x_positions[i], y, h)

    y -= 15

    for d in devices:
        c.drawString(40, y, d["ip"])
        c.drawString(130, y, d["mac"])
        c.drawString(270, y, d["name"][:20])
        c.drawString(420, y, d["zone"])
        c.drawString(480, y, str(d["distance"]))

        y -= 15
        if y < 40:
            c.showPage()
            y = height - 50

    c.save()
    return PDF_PATH
