import atexit
import os
import signal
import time

import requests


def consul_url():
    host = os.environ.get("CONSUL_HOST", "consul")
    port = os.environ.get("CONSUL_PORT", "8500")

    return f"http://{host}:{port}"


def register_service(
    service_name,
    service_id,
    service_address,
    service_port
):
    payload = {
        "ID": service_id,
        "Name": service_name,
        "Address": service_address,
        "Port": int(service_port),
        "Check": {
            "HTTP": (
                f"http://{service_address}:"
                f"{service_port}/health"
            ),
            "Interval": "10s",
            "Timeout": "5s"
        }
    }

    url = (
        f"{consul_url()}"
        "/v1/agent/service/register"
    )

    for attempt in range(1, 31):
        try:
            response = requests.put(
                url,
                json=payload,
                timeout=3
            )

            response.raise_for_status()

            print(
                f"[CONSUL] Servicio registrado: "
                f"{service_name} "
                f"({service_address}:{service_port})"
            )

            return True

        except requests.RequestException as error:

            print(
                f"[CONSUL] Intento {attempt}/30 "
                f"fallido: {error}"
            )

            time.sleep(2)

    print(
        f"[CONSUL] No fue posible registrar "
        f"{service_name}"
    )

    return False


def deregister_service(service_id):
    try:
        requests.put(
            (
                f"{consul_url()}"
                f"/v1/agent/service/deregister/"
                f"{service_id}"
            ),
            timeout=2
        )

        print(
            f"[CONSUL] Servicio eliminado: "
            f"{service_id}"
        )

    except requests.RequestException:
        pass


def setup_deregistration(service_id):
    """
    Se mantiene el registro en Consul cuando el contenedor se detiene.
    De esta forma, el health check de Consul detecta la caída y marca
    el servicio como Critical.
    """
    return
