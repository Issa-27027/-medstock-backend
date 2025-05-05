CREATE DATABASE IF NOT EXISTS medstock_db;
CREATE USER IF NOT EXISTS 'django_user'@'localhost' IDENTIFIED BY 'khazam2004';
GRANT ALL PRIVILEGES ON medstock_db.* TO 'django_user'@'localhost';
FLUSH PRIVILEGES;