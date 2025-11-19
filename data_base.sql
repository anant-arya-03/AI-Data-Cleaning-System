DROP DATABASE IF EXISTS data_cleaning_system;
CREATE DATABASE data_cleaning_system;
USE data_cleaning_system;

CREATE TABLE customer_data (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50),
  email VARCHAR(100),
  age INT,
  salary FLOAT
);

INSERT INTO customer_data (name, email, age, salary) VALUES
('Anant','anant@gmail.com',22,50000),
('Anant','anant@gmail.com',22,50000),
('Rohan',NULL,25,45000),
('Neha','neha@gmail.com',NULL,30000),
('Amit','amit@gmail.com',35,1000000),
('Sujal','sujal@gmail.com',29,62000);
