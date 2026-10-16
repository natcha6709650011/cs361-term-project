USE cstu_room_db;

CREATE TABLE IF NOT EXISTS rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    room_number INT NOT NULL UNIQUE,
    room_type_id INT NOT NULL,
    floor INT NOT NULL,
    capacity INT DEFAULT NULL,
    caretaker_name VARCHAR(100) DEFAULT NULL,
    image_url VARCHAR(500) DEFAULT NULL,
    amenities_json JSON DEFAULT NULL,
    is_partitionable BOOLEAN DEFAULT FALSE,
    is_permanent_locked BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_bookable BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_rooms_room_type 
        FOREIGN KEY (room_type_id) REFERENCES room_types(room_type_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

INSERT IGNORE INTO rooms (
    room_number, room_type_id, floor, capacity, caretaker_name, 
    image_url, amenities_json, 
    is_partitionable, is_permanent_locked, is_active, is_bookable
) VALUES 
(
    106, 5, 1, NULL, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_134938.jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    107, 2, 1, 83, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_134750.jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "คอมพิวเตอร์"}, {"item": "โปรเจคเตอร์"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    111, 2, 1, NULL, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_135153.jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "คอมพิวเตอร์"}, {"item": "โปรเจคเตอร์"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    213, 2, 2, 60, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_135400.jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "คอมพิวเตอร์"}, {"item": "โปรเจคเตอร์"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    214, 3, 2, NULL, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_140251.jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "ทีวี"}, {"item": "ปลั๊กไฟ"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    215, 3, 2, NULL, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_140251.jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "ทีวี"}, {"item": "ปลั๊กไฟ"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    301, 3, 3, 8, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_140251.jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "ทีวี"}, {"item": "ปลั๊กไฟ"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    302, 3, 3, 8, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_140251.jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "ทีวี"}, {"item": "ปลั๊กไฟ"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    303, 3, 3, 8, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_140251.jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "ทีวี"}, {"item": "ปลั๊กไฟ"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    304, 3, 3, 8, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_140251.jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "ทีวี"}, {"item": "ปลั๊กไฟ"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    305, 3, 3, 4, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_140251.jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "ทีวี"}, {"item": "ปลั๊กไฟ"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    306, 1, 3, 48, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_140041+(1).jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "คอมพิวเตอร์"}, {"item": "โปรเจคเตอร์"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    307, 4, 3, 32, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_135823.jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "ปลั๊กไฟ"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    308, 1, 3, 70, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_140041+(1).jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "คอมพิวเตอร์"}, {"item": "โปรเจคเตอร์"}]', 
    TRUE, FALSE, TRUE, TRUE
),
(
    309, 1, 3, 70, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_140041+(1).jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "คอมพิวเตอร์"}, {"item": "โปรเจคเตอร์"}]', 
    TRUE, FALSE, TRUE, TRUE
),
(
    310, 1, 3, 70, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_140041+(1).jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "คอมพิวเตอร์"}, {"item": "โปรเจคเตอร์"}]', 
    TRUE, FALSE, TRUE, TRUE
),
(
    311, 1, 3, 35, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_140041+(1).jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "คอมพิวเตอร์"}, {"item": "โปรเจคเตอร์"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    312, 1, 3, 35, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_140041+(1).jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "คอมพิวเตอร์"}, {"item": "โปรเจคเตอร์"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    313, 4, 3, 54, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_135823.jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "ปลั๊กไฟ"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    314, 3, 3, 8, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_140251.jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "ทีวี"}, {"item": "ปลั๊กไฟ"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    315, 3, 3, 8, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_140251.jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "ทีวี"}, {"item": "ปลั๊กไฟ"}]', 
    FALSE, FALSE, TRUE, TRUE
),
(
    316, 3, 3, 8, NULL, 
    'https://cstu-room-images1.s3.us-east-1.amazonaws.com/20260826_140251.jpg', '[{"item": "โต๊ะ"}, {"item": "เก้าอี้"}, {"item": "ทีวี"}, {"item": "ปลั๊กไฟ"}]', 
    FALSE, FALSE, TRUE, TRUE
);
