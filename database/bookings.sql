USE cstu_room_db;

CREATE TABLE IF NOT EXISTS bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    status ENUM('pending', 'approved', 'cancelled') NOT NULL DEFAULT 'approved',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_bookings_room 
        FOREIGN KEY (room_id) REFERENCES rooms(room_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
        
    INDEX idx_bookings_lookup (room_id, start_time, end_time, status)
);

-- Mock ข้อมูลการจองห้อง
INSERT INTO bookings (room_id, title, start_time, end_time, status) VALUES
(
    (SELECT room_id FROM rooms WHERE room_number = 306),
    'CS361 Software Engineering (บรรยาย)',
    CONCAT(CURDATE(), ' 08:00:00'),
    CONCAT(CURDATE(), ' 11:00:00'),
    'approved'
),

(
    (SELECT room_id FROM rooms WHERE room_number = 306),
    'นัดปรึกษาโครงงานพิเศษกลุ่ม 4',
    CONCAT(CURDATE(), ' 11:00:00'),
    CONCAT(CURDATE(), ' 12:30:00'),
    'approved'
),

(
    (SELECT room_id FROM rooms WHERE room_number = 107),
    'ชุมนุมคอมพิวเตอร์จัดติวทบทวน',
    CONCAT(CURDATE(), ' 13:30:00'),
    CONCAT(CURDATE(), ' 15:00:00'),
    'pending'
),

(
    (SELECT room_id FROM rooms WHERE room_number = 107),
    'ยกเลิกการบรรยายพิเศษ',
    CONCAT(CURDATE(), ' 15:00:00'),
    CONCAT(CURDATE(), ' 16:30:00'),
    'cancelled'
),

(
    (SELECT room_id FROM rooms WHERE room_number = 107),
    'CS231 ปฏิบัติการโครงสร้างข้อมูล',
    CONCAT(DATE_ADD(CURDATE(), INTERVAL 1 DAY), ' 09:30:00'),
    CONCAT(DATE_ADD(CURDATE(), INTERVAL 1 DAY), ' 12:30:00'),
    'approved'
);