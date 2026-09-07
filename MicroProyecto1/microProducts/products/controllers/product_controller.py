from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from db.db import db
from products.models.product_model import Product


product_controller = Blueprint("product_controller", __name__)


@product_controller.route("/api/products", methods=["GET"])
def get_products():
    products = Product.query.order_by(Product.id).all()
    return jsonify([product.to_dict() for product in products]), 200


@product_controller.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"message": "Producto no encontrado"}), 404

    return jsonify(product.to_dict()), 200


@product_controller.route("/api/products", methods=["POST"])
def create_product():
    data = request.get_json(silent=True) or {}

    name = data.get("name")
    price = data.get("price")
    quantity = data.get("quantity")

    if not name or price is None or quantity is None:
        return jsonify({"message": "Información de producto inválida"}), 400

    try:
        price = Decimal(str(price))
        quantity = int(quantity)

        if price < 0 or quantity < 0:
            raise ValueError
    except (ValueError, TypeError, InvalidOperation):
        return jsonify({"message": "Precio o cantidad inválidos"}), 400

    product = Product(
        name=name,
        price=price,
        quantity=quantity
    )

    db.session.add(product)
    db.session.commit()

    return jsonify(product.to_dict()), 201


@product_controller.route("/api/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"message": "Producto no encontrado"}), 404

    data = request.get_json(silent=True) or {}

    try:
        if "name" in data:
            if not data["name"]:
                return jsonify({"message": "Nombre inválido"}), 400
            product.name = data["name"]

        if "price" in data:
            price = Decimal(str(data["price"]))
            if price < 0:
                raise ValueError
            product.price = price

        if "quantity" in data:
            quantity = int(data["quantity"])
            if quantity < 0:
                raise ValueError
            product.quantity = quantity

    except (ValueError, TypeError, InvalidOperation):
        db.session.rollback()
        return jsonify({"message": "Precio o cantidad inválidos"}), 400

    db.session.commit()

    return jsonify(product.to_dict()), 200


@product_controller.route("/api/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"message": "Producto no encontrado"}), 404

    db.session.delete(product)
    db.session.commit()

    return jsonify({"message": "Producto eliminado correctamente"}), 200


@product_controller.route("/api/products/inventory/reserve", methods=["POST"])
def reserve_inventory():
    data = request.get_json(silent=True) or {}
    requested_products = data.get("products")

    if not requested_products or not isinstance(requested_products, list):
        return jsonify({"message": "Información de productos inválida"}), 400

    quantities = {}

    try:
        for item in requested_products:
            product_id = int(item.get("product_id"))
            quantity = int(item.get("quantity"))

            if product_id <= 0 or quantity <= 0:
                raise ValueError

            quantities[product_id] = quantities.get(product_id, 0) + quantity

    except (TypeError, ValueError, AttributeError):
        return jsonify({"message": "Producto o cantidad inválida"}), 400

    product_ids = sorted(quantities.keys())

    try:
        statement = (
            select(Product)
            .where(Product.id.in_(product_ids))
            .order_by(Product.id)
            .with_for_update()
        )

        products = db.session.execute(statement).scalars().all()

        found_products = {product.id: product for product in products}

        missing = [
            product_id
            for product_id in product_ids
            if product_id not in found_products
        ]

        if missing:
            db.session.rollback()
            return jsonify({
                "message": "Producto no existe",
                "product_ids": missing
            }), 404

        insufficient = []

        for product_id in product_ids:
            product = found_products[product_id]
            requested_quantity = quantities[product_id]

            if product.quantity < requested_quantity:
                insufficient.append({
                    "product_id": product_id,
                    "available": product.quantity,
                    "requested": requested_quantity
                })

        if insufficient:
            db.session.rollback()
            return jsonify({
                "message": "Inventario insuficiente",
                "products": insufficient
            }), 409

        reserved = []

        for product_id in product_ids:
            product = found_products[product_id]
            requested_quantity = quantities[product_id]

            product.quantity -= requested_quantity

            reserved.append({
                "product_id": product.id,
                "name": product.name,
                "quantity": requested_quantity,
                "unit_price": float(product.price),
                "remaining_stock": product.quantity
            })

        db.session.commit()

        return jsonify({
            "message": "Inventario reservado correctamente",
            "products": reserved
        }), 200

    except Exception as error:
        db.session.rollback()

        print(f"[PRODUCTS] Error reservando inventario: {error}")

        return jsonify({
            "message": "Error interno al actualizar inventario"
        }), 500


@product_controller.route("/api/products/inventory/release", methods=["POST"])
def release_inventory():
    data = request.get_json(silent=True) or {}
    requested_products = data.get("products")

    if not requested_products or not isinstance(requested_products, list):
        return jsonify({
            "message": "Informacion de productos invalida"
        }), 400

    quantities = {}

    try:
        for item in requested_products:
            product_id = int(item.get("product_id"))
            quantity = int(item.get("quantity"))

            if product_id <= 0 or quantity <= 0:
                raise ValueError

            quantities[product_id] = (
                quantities.get(product_id, 0)
                + quantity
            )

    except (TypeError, ValueError, AttributeError):
        return jsonify({
            "message": "Producto o cantidad invalida"
        }), 400

    product_ids = sorted(quantities.keys())

    try:
        statement = (
            select(Product)
            .where(Product.id.in_(product_ids))
            .order_by(Product.id)
            .with_for_update()
        )

        products = (
            db.session.execute(statement)
            .scalars()
            .all()
        )

        found_products = {
            product.id: product
            for product in products
        }

        missing = [
            product_id
            for product_id in product_ids
            if product_id not in found_products
        ]

        if missing:
            db.session.rollback()

            return jsonify({
                "message": "Producto no existe",
                "product_ids": missing
            }), 404

        released = []

        for product_id in product_ids:
            product = found_products[product_id]
            quantity = quantities[product_id]

            product.quantity += quantity

            released.append({
                "product_id": product.id,
                "quantity": quantity,
                "current_stock": product.quantity
            })

        db.session.commit()

        return jsonify({
            "message": "Inventario liberado correctamente",
            "products": released
        }), 200

    except Exception as error:
        db.session.rollback()

        print(
            f"[PRODUCTS] Error liberando inventario: {error}"
        )

        return jsonify({
            "message": "Error interno al liberar inventario"
        }), 500
