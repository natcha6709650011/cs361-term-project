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

-- คำสั่ง query
-- query 1 : ค้นหาห้องว่างตาม วัน, เวลา, ประเภทห้อง และความจุ
SET @req_start    = CONCAT(CURDATE(), ' 09:30:00');
SET @req_end      = CONCAT(CURDATE(), ' 11:00:00'); 
SET @room_type_id = 1;                              
SET @min_capacity = 40;                             

SELECT 
    r.room_id,
    r.room_number,
    r.floor,
    r.capacity,
    rt.type_name
FROM rooms r
JOIN room_types rt ON r.room_type_id = rt.room_type_id
WHERE r.is_active = TRUE
  AND r.is_permanent_locked = FALSE
  AND (@room_type_id IS NULL OR r.room_type_id = @room_type_id)
  AND (@min_capacity IS NULL OR r.capacity >= @min_capacity)
  AND r.room_id NOT IN (
      SELECT b.room_id
      FROM bookings b
      WHERE b.status IN ('approved', 'pending')
        AND b.start_time < @req_end
        AND b.end_time > @req_start
  )
ORDER BY r.room_number ASC;

-- query 2 : ดึงข้อมูลการจองห้องในวันที่กำหนด
SET @target_room_number = 306;
SET @target_date        = CURDATE();

SELECT 
    b.booking_id,
    r.room_number,
    b.title,
    b.start_time,
    b.end_time,
    b.status
FROM bookings b
JOIN rooms r ON b.room_id = r.room_id
WHERE r.room_number = @target_room_number
  AND DATE(b.start_time) = @target_date
  AND b.status IN ('approved', 'pending')
ORDER BY b.start_time ASC;

-- query 3 : ตรวจสอบเคสการจองที่ขอบเวลาชนกันพอดี
SELECT 
    b.booking_id,
    b.title,
    b.start_time,
    b.end_time,
    b.status
FROM bookings b
JOIN rooms r ON b.room_id = r.room_id
WHERE r.room_number = 306
  AND b.start_time < CONCAT(CURDATE(), ' 12:30:00')
  AND b.end_time > CONCAT(CURDATE(), ' 11:00:00');
