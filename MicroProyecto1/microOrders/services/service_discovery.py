import os
import requests


class ServiceDiscoveryError(Exception):
    pass


def discover_service(service_name):
    consul_host = os.environ["CONSUL_HOST"]
    consul_port = os.environ["CONSUL_PORT"]

    url = (
        f"http://{consul_host}:{consul_port}"
        f"/v1/health/service/{service_name}"
    )

    try:
        response = requests.get(
            url,
            params={"passing": "true"},
            timeout=3
        )

        response.raise_for_status()

        services = response.json()

    except requests.RequestException as error:
        raise ServiceDiscoveryError(
            f"No fue posible consultar Consul: {error}"
        ) from error

    if not services:
        raise ServiceDiscoveryError(
            f"No hay instancias saludables del servicio '{service_name}'"
        )

    selected = services[0]

    service = selected.get("Service", {})

    address = (
        service.get("Address")
        or selected.get("Node", {}).get("Address")
    )

    port = service.get("Port")

    if not address or not port:
        raise ServiceDiscoveryError(
            f"Consul devolvio informacion incompleta para '{service_name}'"
        )

    print(
        f"[DISCOVERY] Servicio '{service_name}' "
        f"resuelto por Consul -> {address}:{port}"
    )

    return f"http://{address}:{port}"
