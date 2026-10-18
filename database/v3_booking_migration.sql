-- V3 booking ownership migration
-- Run this file ONCE in DBeaver after selecting the cstu_room_db database.
--
-- Why this is needed:
-- Every new booking must be linked to the logged-in user.  The Booking
-- Lambda can then list only that user's bookings and reject an attempt to
-- edit or cancel someone else's booking (BOLA protection).

USE cstu_room_db;

-- Keep this column nullable temporarily so existing sample bookings, which
-- were created before V3 login, are not deleted or made invalid.  The V3
-- Booking API must always insert a non-NULL user_id for every NEW booking.
ALTER TABLE bookings
    ADD COLUMN user_id INT NULL AFTER room_id;

-- `title` already stores the booking purpose.  Keep the attendee count in a
-- separate field because it is needed for capacity validation and My Bookings.
ALTER TABLE bookings
    ADD COLUMN participant_count INT NULL AFTER title;

ALTER TABLE bookings
    ADD CONSTRAINT fk_bookings_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE;

CREATE INDEX idx_bookings_user_id ON bookings (user_id);

-- Verification: confirm that the column and foreign key were added.
SHOW COLUMNS FROM bookings LIKE 'user_id';

SELECT
    CONSTRAINT_NAME,
    TABLE_NAME,
    REFERENCED_TABLE_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'bookings'
  AND COLUMN_NAME = 'user_id';
