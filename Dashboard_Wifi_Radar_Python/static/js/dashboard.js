let radar;

function loadDevices() {
    fetch("/api/devices")
        .then(res => res.json())
        .then(data => {
            updateTable(data.devices);
            updateRadar(data.devices);

            if (data.new_devices.length > 0) {
                document.getElementById("alert").innerHTML =
                    "!! Nuevo dispositivo conectado: " + data.new_devices.join(", ");
            }
        });
}

function updateTable(devices) {
    const tbody = document.querySelector("#deviceTable tbody");
    tbody.innerHTML = "";

    devices.forEach(d => {
        tbody.innerHTML += `
            <tr>
                <td>${d.ip}</td>
                <td>${d.mac}</td>
                <td>${d.name}</td>
                <td>${d.zone}</td>
                <td>${d.distance}</td>
            </tr>
        `;
    });
}

function updateRadar(devices) {
    const labels = devices.map(d => d.name || d.ip);
    const distances = devices.map(d => d.distance);

    if (radar) radar.destroy();

    radar = new Chart(document.getElementById("radarChart"), {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: "Distancia estimada (m)",
                data: distances,
                backgroundColor: 'rgba(255,0,0,0.2)',
                borderColor: 'rgba(255,0,0,1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                r: {
                    angleLines: {
                        color: 'red'
                    },
                    grid: {
                        color: 'red'
                    },
                    pointLabels: {
                        color: 'red',
                        font: {
                            size: 12
                        }
                    },
                    ticks: {
                        color: 'red'
                    }
                }
            },
            plugins: {
                datalabels: {
                    color: 'red',  // texto fijo sobre cada punto
                    align: 'top',
                    formatter: function(value, context) {
                        const d = devices[context.dataIndex];
                        return [
                            `Nombre: ${d.name}`,
                            `IP: ${d.ip}`,
                            `MAC: ${d.mac}`,
                            `Distancia: ${d.distance} m`
                        ];
                    },
                    font: {
                        size: 10
                    }
                },
                legend: {
                    labels: {
                        color: 'red'
                    }
                },
                tooltip: {
                    titleColor: 'red',
                    bodyColor: 'red',
                    backgroundColor: '#000'
                }
            }
        },
        plugins: [ChartDataLabels]
    });
}

setInterval(loadDevices, 10000);
loadDevices();
