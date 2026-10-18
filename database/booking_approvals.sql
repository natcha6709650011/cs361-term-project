USE cstu_room_db;

-- History of decisions made by users with the APPROVER role.
CREATE TABLE IF NOT EXISTS booking_approvals (
    approval_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    approver_id INT NOT NULL,
    action ENUM('APPROVED', 'REJECTED') NOT NULL,
    reason VARCHAR(500) NULL,
    approved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_booking_approvals_booking
        FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_booking_approvals_user
        FOREIGN KEY (approver_id) REFERENCES users(user_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_approval_booking_time (booking_id, approved_at)
);
