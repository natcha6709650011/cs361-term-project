-- V4 Check-in and automatic booking completion
-- Run ONCE against cstu_room_db.
-- No manual Check-out or actual_usage_end column is required.

USE cstu_room_db;

ALTER TABLE bookings
    MODIFY COLUMN status ENUM(
        'pending',
        'approved',
        'rejected',
        'cancelled',
        'no_show'
    ) NOT NULL DEFAULT 'pending';

ALTER TABLE bookings
    ADD COLUMN attendance_status ENUM(
        'NOT_CHECKED_IN',
        'CHECKED_IN',
        'NO_SHOW',
        'COMPLETED'
    ) NOT NULL DEFAULT 'NOT_CHECKED_IN' AFTER status,
    ADD COLUMN checked_in_at DATETIME NULL AFTER attendance_status,
    ADD COLUMN actual_usage_start DATETIME NULL AFTER checked_in_at,
    ADD COLUMN no_show_at DATETIME NULL AFTER actual_usage_start;

CREATE INDEX idx_bookings_no_show
    ON bookings (status, attendance_status, start_time);

-- Verify columns
SHOW COLUMNS FROM bookings LIKE 'attendance_status';
SHOW COLUMNS FROM bookings LIKE 'checked_in_at';
SHOW COLUMNS FROM bookings LIKE 'actual_usage_start';
SHOW COLUMNS FROM bookings LIKE 'no_show_at';