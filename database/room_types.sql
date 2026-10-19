CREATE DATABASE IF NOT EXISTS cstu_room_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE cstu_room_db;

CREATE TABLE IF NOT EXISTS room_types (
    room_type_id INT AUTO_INCREMENT PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL
);

INSERT IGNORE INTO room_types (room_type_id, type_name) VALUES
(1, 'ห้องเรียน'),
(2, 'ห้องปฏิบัติการคอมพิวเตอร์'),
(3, 'ห้องประชุม'),
(4, 'Co-Working Space'),
(5, 'ห้องกิจกรรมนักศึกษา'),
(6, 'ห้องแลปเฉพาะทาง'),
(7, 'ห้องพักอาจารย์'),
(8, 'ห้องพักบัณฑิตศึกษา'),
(9, 'ห้องอ่านหนังสือ');
