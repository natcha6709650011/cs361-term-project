-- V4 booking request note
-- Run once in DBeaver after selecting cstu_room_db, before deploying the
-- updated Booking and Booking Facility Management Lambdas.

USE cstu_room_db;

ALTER TABLE bookings
    ADD COLUMN request_note VARCHAR(500) NULL AFTER title;

-- Verification
SHOW COLUMNS FROM bookings LIKE 'request_note';
