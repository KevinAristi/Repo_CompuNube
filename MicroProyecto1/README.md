# Micro Proyecto 1 — Computación en la Nube

Sistema de administración de usuarios, productos y órdenes de compra implementado con microservicios independientes, persistencia desacoplada, Docker Compose y descubrimiento dinámico de servicios mediante Consul.

## Arquitectura

Se implementó la arquitectura propuesta en el parcial:

```text
Frontend :8080

Users :5002      Products :5003      Orders :5004
    |                 |                  |
 users_db        products_db         orders_db

                Consul :8500
```

Cada microservicio utiliza su propia base de datos MySQL y la comunicación entre servicios se realiza mediante API HTTP.

`microOrders` descubre dinámicamente a `microProducts` mediante Consul antes de consultar productos o actualizar inventario.

## Levantar el proyecto

```bash
git clone https://github.com/KevinAristi/Repo_CompuNube.git
cd Repo_CompuNube/MicroProyecto1

cp .env.example .env

docker compose up --build -d
```

Frontend:

```text
http://localhost:8080
```

Consul:

```text
http://localhost:8500/ui/
```

En el entorno Vagrant utilizado durante el desarrollo:

```text
Frontend: http://192.168.100.3:8080
Consul:   http://192.168.100.3:8500/ui/
```

Usuarios de prueba:

```text
juan / 123
maria / 456
```

## Microservicio de órdenes

Endpoints principales:

```text
GET  /api/orders
GET  /api/orders/<id>
POST /api/orders
```

La creación de órdenes obtiene el usuario desde la sesión, consulta precio y existencias en Products, valida el inventario, calcula el total, descuenta stock y guarda la orden junto con sus ítems.

Errores manejados:

| Código | Situación |
|---|---|
| 400 | Petición inválida |
| 401 | Sin sesión válida |
| 404 | Producto inexistente |
| 409 | Inventario insuficiente |
| 500 | Products no disponible o error interno |

## Persistencia

Cada base de datos utiliza un volumen nombrado.

La persistencia puede comprobarse con:

```bash
docker compose down
docker compose up -d
```

Los usuarios, productos y órdenes deben conservarse después del reinicio.

## Consul y resiliencia

Los microservicios `users`, `products` y `orders` se registran automáticamente en Consul y exponen `/health`.

Para comprobar el descubrimiento dinámico:

```bash
docker compose logs --tail=100 microorders | grep DISCOVERY
```

Para probar resiliencia:

```bash
docker compose stop microproducts
```

Después de unos segundos, Products debe aparecer como `Critical` en Consul y la creación de una orden debe responder de forma controlada con HTTP `500`.

Para recuperarlo:

```bash
docker compose up -d microproducts
```

Products debe volver a `Passing` y Orders debe poder crear órdenes nuevamente.

## Declaración de uso de IA

Durante el desarrollo se utilizó **ChatGPT de OpenAI** y Claude como herramienta de apoyo para la implementación, configuración de Docker Compose y Consul, integración de microservicios, diagnóstico de errores y documentación.
El código y las configuraciones fueron revisados y probados durante el desarrollo.
