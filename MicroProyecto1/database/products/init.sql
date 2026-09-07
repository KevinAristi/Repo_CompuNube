USE products_db;

CREATE TABLE IF NOT EXISTS products (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL DEFAULT 0
);

INSERT INTO products (name, price, quantity)
VALUES
    ('Producto A', 25.50, 20),
    ('Producto B', 40.00, 15),
    ('Producto C', 12.75, 30),
    ('Producto D', 80.00, 5);
