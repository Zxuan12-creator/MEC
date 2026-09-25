CREATE DATABASE IF NOT EXISTS mec_mart CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE mec_mart;

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS daily_counters;
DROP TABLE IF EXISTS products;

CREATE TABLE products (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(100) NOT NULL,
 category ENUM('minuman','makanan','batik') NOT NULL,
 price INT DEFAULT NULL,
 available TINYINT(1) NOT NULL DEFAULT 1,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE daily_counters (
 counter_date DATE PRIMARY KEY,
 last_number INT NOT NULL DEFAULT 0
) ENGINE=InnoDB;

CREATE TABLE orders (
 id INT AUTO_INCREMENT PRIMARY KEY,
 order_number VARCHAR(50) NOT NULL UNIQUE,
 queue_number INT NOT NULL,
 queue_date DATE NOT NULL,
 customer_name VARCHAR(100) NOT NULL,
 phone VARCHAR(30) NOT NULL,
 address TEXT,
 class_name VARCHAR(100),
 note TEXT,
 subtotal INT NOT NULL DEFAULT 0,
 delivery_fee INT NOT NULL DEFAULT 0,
 total INT NOT NULL DEFAULT 0,
 delivery_method ENUM('pickup','delivery') NOT NULL DEFAULT 'pickup',
 payment_method ENUM('qris','cod') NOT NULL,
 payment_status ENUM('pending','paid','failed') NOT NULL DEFAULT 'pending',
 status ENUM('waiting','making','ready','done') NOT NULL DEFAULT 'waiting',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 INDEX idx_orders_phone (phone),
 INDEX idx_orders_queue_date (queue_date)
) ENGINE=InnoDB;

CREATE TABLE order_items (
 id INT AUTO_INCREMENT PRIMARY KEY,
 order_id INT NOT NULL,
 product_id INT DEFAULT NULL,
 product_name VARCHAR(100) NOT NULL,
 price INT NOT NULL,
 quantity INT NOT NULL,
 subtotal INT NOT NULL,
 section ENUM('minuman','makanan') NOT NULL,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE ON UPDATE CASCADE,
 FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL ON UPDATE CASCADE,
 INDEX idx_order_items_order_id (order_id)
) ENGINE=InnoDB;

INSERT INTO products (name, category, price, available) VALUES
('Thai Tea','minuman',6000,1),('Matcha','minuman',8000,1),('Blackcurrant','minuman',5000,1),('Latte','minuman',6000,1),('Latte + Art','minuman',8000,1),('Chocolate','minuman',6000,1),('Espresso','minuman',8000,1),('Americano','minuman',5000,1),
('Kentang','makanan',NULL,0),('Dimsum','makanan',NULL,0),('Gyoza','makanan',NULL,0),('Dumpling','makanan',NULL,0),('Onigiri','makanan',NULL,0),('Sushi','makanan',NULL,0);
