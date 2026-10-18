USE cstu_room_db;

-- Additive V3 table: weekly recurring fixed facility schedule.
-- This table is intentionally named facility_schedule_rules to avoid colliding
-- with the older facility_schedules table that stores one-off datetime ranges.
CREATE TABLE IF NOT EXISTS facility_schedule_rules (
    schedule_id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    weekday TINYINT NOT NULL COMMENT '0=Monday, 1=Tuesday, ..., 6=Sunday',
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    valid_from DATE NOT NULL,
    valid_until DATE NOT NULL,
    status ENUM('ACTIVE','CANCELLED') NOT NULL DEFAULT 'ACTIVE',
    created_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_facility_rule_weekday CHECK (weekday BETWEEN 0 AND 6),
    CONSTRAINT chk_facility_rule_time CHECK (start_time < end_time),
    CONSTRAINT chk_facility_rule_dates CHECK (valid_from <= valid_until),
    CONSTRAINT fk_facility_rule_room FOREIGN KEY (room_id) REFERENCES rooms(room_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_facility_rule_creator FOREIGN KEY (created_by) REFERENCES users(user_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_facility_rule_lookup (room_id, status, weekday, valid_from, valid_until)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Append-only per-date exceptions. The newest exception_id for a schedule/date
-- is authoritative. RELEASE temporarily opens that one occurrence; RESTORE
-- re-applies the fixed schedule to that date after conflict checks pass.
CREATE TABLE IF NOT EXISTS facility_schedule_exceptions (
    exception_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    schedule_id INT NOT NULL,
    exception_date DATE NOT NULL,
    action ENUM('RELEASE','RESTORE') NOT NULL,
    reason VARCHAR(500) NOT NULL,
    created_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_facility_exception_rule FOREIGN KEY (schedule_id)
        REFERENCES facility_schedule_rules(schedule_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_facility_exception_creator FOREIGN KEY (created_by)
        REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_facility_exception_latest (schedule_id, exception_date, exception_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
