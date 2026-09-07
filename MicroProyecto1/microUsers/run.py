import os

from users.views import app
from services.consul_registration import (
    register_service,
    setup_deregistration
)


if __name__ == "__main__":

    service_name = os.environ.get(
        "SERVICE_NAME",
        "users"
    )

    service_id = os.environ.get(
        "SERVICE_ID",
        "users-1"
    )

    service_address = os.environ.get(
        "SERVICE_ADDRESS",
        "microusers"
    )

    service_port = int(
        os.environ.get(
            "SERVICE_PORT",
            "5002"
        )
    )

    register_service(
        service_name,
        service_id,
        service_address,
        service_port
    )

    setup_deregistration(
        service_id
    )

    app.run(
        host="0.0.0.0",
        port=5002
    )
