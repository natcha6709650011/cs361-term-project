USE cstu_room_db;

-- Audit history for temporary room closures (maintenance/damage) managed by FACILITY_ADMIN.
-- The rooms.is_bookable flag remains the shared source used by the existing availability search.
CREATE TABLE IF NOT EXISTS room_closures (
    closure_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    reason VARCHAR(500) NOT NULL,
    previous_is_bookable BOOLEAN NOT NULL DEFAULT TRUE,
    status ENUM('CLOSED','OPENED') NOT NULL DEFAULT 'CLOSED',
    created_by INT NOT NULL,
    closed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    opened_by INT NULL,
    opening_reason VARCHAR(500) NULL,
    opened_at TIMESTAMP NULL,
    CONSTRAINT fk_room_closures_room FOREIGN KEY (room_id) REFERENCES rooms(room_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_room_closures_created_by FOREIGN KEY (created_by) REFERENCES users(user_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_room_closures_opened_by FOREIGN KEY (opened_by) REFERENCES users(user_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_room_closures_status (room_id, status, closure_id),
    INDEX idx_room_closures_time (closed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
