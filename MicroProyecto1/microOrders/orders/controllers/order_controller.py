from decimal import Decimal, InvalidOperation

import requests

from flask import Blueprint, jsonify, request, session

from db.db import db
from orders.models.order_model import Order, OrderItem
from services.service_discovery import (
    ServiceDiscoveryError,
    discover_service
)


order_controller = Blueprint(
    "order_controller",
    __name__
)


def get_session_user():
    username = session.get("username")
    email = session.get("email")

    if not username or not email:
        return None

    return {
        "username": username,
        "email": email
    }


def response_json(response, default_message):
    try:
        return response.json()
    except ValueError:
        return {
            "message": default_message
        }


@order_controller.route(
    "/api/orders",
    methods=["GET"]
)
def get_all_orders():

    user = get_session_user()

    if not user:
        return jsonify({
            "message": "No hay sesion de usuario valida"
        }), 401

    orders = (
        Order.query
        .filter_by(user_email=user["email"])
        .order_by(Order.created_at.desc())
        .all()
    )

    return jsonify([
        order.to_dict()
        for order in orders
    ]), 200


@order_controller.route(
    "/api/orders/<int:order_id>",
    methods=["GET"]
)
def get_order(order_id):

    user = get_session_user()

    if not user:
        return jsonify({
            "message": "No hay sesion de usuario valida"
        }), 401

    order = db.session.get(
        Order,
        order_id
    )

    if (
        not order
        or order.user_email != user["email"]
    ):
        return jsonify({
            "message": "Orden no encontrada"
        }), 404

    return jsonify(
        order.to_dict(include_items=True)
    ), 200


@order_controller.route(
    "/api/orders",
    methods=["POST"]
)
def create_order():

    # -------------------------------------------------
    # 1. VALIDAR SESION
    # -------------------------------------------------

    user = get_session_user()

    if not user:
        return jsonify({
            "message": "No hay sesion de usuario valida"
        }), 401

    # -------------------------------------------------
    # 2. VALIDAR JSON
    # -------------------------------------------------

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "message": "Peticion mal formada"
        }), 400

    requested_products = data.get("products")

    if (
        not requested_products
        or not isinstance(requested_products, list)
    ):
        return jsonify({
            "message": "Informacion de productos invalida"
        }), 400

    # Agrupar productos repetidos
    quantities = {}

    try:
        for item in requested_products:

            if not isinstance(item, dict):
                raise ValueError

            product_id = int(
                item.get("product_id")
            )

            quantity = int(
                item.get("quantity")
            )

            if (
                product_id <= 0
                or quantity <= 0
            ):
                raise ValueError

            quantities[product_id] = (
                quantities.get(product_id, 0)
                + quantity
            )

    except (
        TypeError,
        ValueError,
        AttributeError
    ):
        return jsonify({
            "message": "Informacion de productos invalida"
        }), 400

    normalized_products = [
        {
            "product_id": product_id,
            "quantity": quantities[product_id]
        }
        for product_id in sorted(
            quantities.keys()
        )
    ]

    # -------------------------------------------------
    # 3. DESCUBRIR PRODUCTS MEDIANTE CONSUL
    # -------------------------------------------------

    try:
        products_url = discover_service(
            "products"
        )

    except ServiceDiscoveryError as error:

        print(
            f"[ORDERS] Error de discovery: {error}"
        )

        return jsonify({
            "message":
                "Servicio de productos no disponible"
        }), 500

    # -------------------------------------------------
    # 4. CONSULTAR PRODUCTOS
    # -------------------------------------------------

    product_details = []

    total = Decimal("0.00")

    try:
        for item in normalized_products:

            product_id = item["product_id"]
            quantity = item["quantity"]

            response = requests.get(
                f"{products_url}"
                f"/api/products/{product_id}",
                timeout=4
            )

            if response.status_code == 404:

                return jsonify({
                    "message": "Producto no existe",
                    "product_id": product_id
                }), 404

            if response.status_code != 200:

                print(
                    "[ORDERS] Products respondio "
                    f"{response.status_code}"
                )

                return jsonify({
                    "message":
                        "Servicio de productos no disponible"
                }), 500

            product = response.json()

            available = int(
                product["quantity"]
            )

            if available < quantity:

                return jsonify({
                    "message":
                        "Inventario insuficiente",
                    "product_id":
                        product_id,
                    "available":
                        available,
                    "requested":
                        quantity
                }), 409

            try:
                unit_price = Decimal(
                    str(product["price"])
                )

            except (
                InvalidOperation,
                TypeError,
                ValueError
            ):
                return jsonify({
                    "message":
                        "Precio de producto invalido"
                }), 500

            subtotal = (
                unit_price
                * quantity
            ).quantize(
                Decimal("0.01")
            )

            total += subtotal

            product_details.append({
                "product_id":
                    product_id,
                "quantity":
                    quantity,
                "unit_price":
                    unit_price,
                "subtotal":
                    subtotal
            })

    except requests.RequestException as error:

        print(
            "[ORDERS] Error consultando "
            f"Products: {error}"
        )

        return jsonify({
            "message":
                "Servicio de productos no disponible"
        }), 500

    total = total.quantize(
        Decimal("0.01")
    )

    # -------------------------------------------------
    # 5. RESERVAR INVENTARIO DE FORMA ATOMICA
    # -------------------------------------------------

    try:
        reserve_response = requests.post(
            f"{products_url}"
            "/api/products/inventory/reserve",
            json={
                "products":
                    normalized_products
            },
            timeout=5
        )

    except requests.RequestException as error:

        print(
            "[ORDERS] Error reservando "
            f"inventario: {error}"
        )

        return jsonify({
            "message":
                "Servicio de productos no disponible"
        }), 500

    if reserve_response.status_code == 404:

        return jsonify(
            response_json(
                reserve_response,
                "Producto no existe"
            )
        ), 404

    if reserve_response.status_code == 409:

        return jsonify(
            response_json(
                reserve_response,
                "Inventario insuficiente"
            )
        ), 409

    if reserve_response.status_code != 200:

        print(
            "[ORDERS] Error de Products "
            "al reservar inventario: "
            f"{reserve_response.status_code}"
        )

        return jsonify({
            "message":
                "Error al actualizar inventario"
        }), 500

    # -------------------------------------------------
    # 6. CREAR ORDER + ITEMS
    # -------------------------------------------------

    try:
        order = Order(
            user_name=user["username"],
            user_email=user["email"],
            total=total,
            status="CONFIRMED"
        )

        db.session.add(order)

        # Obtener el ID sin hacer commit
        db.session.flush()

        for item in product_details:

            order_item = OrderItem(
                order_id=order.id,
                product_id=(
                    item["product_id"]
                ),
                quantity=(
                    item["quantity"]
                ),
                unit_price=(
                    item["unit_price"]
                ),
                subtotal=(
                    item["subtotal"]
                )
            )

            db.session.add(
                order_item
            )

        db.session.commit()

        print(
            f"[ORDERS] Orden {order.id} "
            "creada exitosamente"
        )

        return jsonify(
            order.to_dict(
                include_items=True
            )
        ), 201

    except Exception as error:

        db.session.rollback()

        print(
            "[ORDERS] Fallo guardando orden: "
            f"{error}"
        )

        # ---------------------------------------------
        # COMPENSACION
        # ---------------------------------------------
        # Products ya desconto inventario.
        # Si Orders no pudo persistir la orden,
        # intentamos devolverlo.
        # ---------------------------------------------

        try:
            compensation = requests.post(
                f"{products_url}"
                "/api/products/inventory/release",
                json={
                    "products":
                        normalized_products
                },
                timeout=5
            )

            print(
                "[ORDERS] Compensacion "
                "de inventario -> HTTP "
                f"{compensation.status_code}"
            )

        except requests.RequestException as compensation_error:

            print(
                "[ORDERS] ERROR CRITICO: "
                "no fue posible compensar "
                "inventario: "
                f"{compensation_error}"
            )

        return jsonify({
            "message":
                "Error interno creando la orden"
        }), 500
