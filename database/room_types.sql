CREATE DATABASE IF NOT EXISTS cstu_room_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE cstu_room_db;

CREATE TABLE IF NOT EXISTS room_types (
    room_type_id INT AUTO_INCREMENT PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL,
    is_bookable BOOLEAN DEFAULT TRUE,
    allowed_roles_json JSON NOT NULL
);

INSERT IGNORE INTO room_types (room_type_id, type_name, is_bookable, allowed_roles_json) VALUES
(1, 'ห้องเรียน', TRUE, '["teacher", "staff"]'),
(2, 'ห้องปฏิบัติการคอมพิวเตอร์', TRUE, '["teacher", "staff"]'),
(3, 'ห้องประชุม', TRUE, '["teacher", "staff", "undergrad", "grad", "phd"]'),
(4, 'Co-Working Space', TRUE, '["grad", "phd"]'),
(5, 'ห้องกิจกรรมนักศึกษา', TRUE, '["teacher", "staff", "undergrad", "grad", "phd"]'),
(6, 'ห้องแลปเฉพาะทาง', FALSE, '[]'),
(7, 'ห้องพักอาจารย์', FALSE, '[]'),
(8, 'ห้องพักบัณฑิตศึกษา', FALSE, '[]'),
(9, 'ห้องอ่านหนังสือ', FALSE, '[]');
