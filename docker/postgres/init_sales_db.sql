-- Create Database
CREATE DATABASE sales_data;
\c sales_data;

-- Tables
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    country VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(50),
    price DECIMAL(10,2)
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    product_id INTEGER REFERENCES products(id),
    status VARCHAR(20),
    amount DECIMAL(10,2),
    order_date DATE
);

CREATE TABLE support_tickets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    subject VARCHAR(200),
    priority VARCHAR(10),
    status VARCHAR(20)
);

-- Seed Data (Users)
INSERT INTO users (name, email, country, created_at) VALUES 
('Juan Perez', 'juan@example.com', 'Mexico', '2025-01-10'),
('Ana Gomez', 'ana@example.com', 'Spain', '2025-02-15'),
('John Doe', 'john@example.com', 'USA', '2025-03-20'),
('Maria Silva', 'maria@example.com', 'Brazil', '2025-04-05'),
('Li Wei', 'li@example.com', 'China', '2025-05-12');

-- Seed Data (Products)
INSERT INTO products (name, category, price) VALUES 
('Laptop Pro', 'Electronics', 1200.00),
('Smartphone Ultra', 'Electronics', 800.00),
('Desk Chair', 'Furniture', 150.00),
('Wireless Mouse', 'Accessories', 25.00),
('Coffee Maker', 'Appliances', 45.00);

-- Seed Data (Orders - Last 12 months simulation)
DO $$
BEGIN
    FOR i IN 1..100 LOOP
        INSERT INTO orders (user_id, product_id, status, amount, order_date)
        VALUES (
            (random() * 4 + 1)::int,
            (random() * 4 + 1)::int,
            CASE WHEN i % 10 = 0 THEN 'cancelled' ELSE 'completed' END,
            (random() * 500 + 50)::decimal(10,2),
            CURRENT_DATE - (random() * 365)::int * interval '1 day'
        );
    END LOOP;
END $$;

-- Prediction Table (for ML pipeline)
CREATE TABLE ml_prediccion_ventas (
    id SERIAL PRIMARY KEY,
    fecha DATE,
    prediccion_monto DECIMAL(10,2),
    timestamp_ejecucion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
