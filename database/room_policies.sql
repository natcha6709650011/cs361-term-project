CREATE TABLE room_policies (
    policy_id INT AUTO_INCREMENT PRIMARY KEY,
    room_type_id INT NOT NULL,
    user_type VARCHAR(30) NOT NULL,
    is_allowed BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_room_policies_room_type
        FOREIGN KEY (room_type_id)
        REFERENCES room_types(room_type_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_room_type_user_type
        UNIQUE (room_type_id, user_type)
);

INSERT INTO room_policies
    (room_type_id, user_type, is_allowed)
VALUES
    (1, 'employee', TRUE),
    (1, 'undergraduate', FALSE),
    (1, 'master', FALSE),
    (1, 'doctoral', FALSE),

    (2, 'employee', TRUE),
    (2, 'undergraduate', FALSE),
    (2, 'master', FALSE),
    (2, 'doctoral', FALSE),

    (3, 'employee', TRUE),
    (3, 'undergraduate', TRUE),
    (3, 'master', TRUE),
    (3, 'doctoral', TRUE),

    (4, 'employee', FALSE),
    (4, 'undergraduate', FALSE),
    (4, 'master', TRUE),
    (4, 'doctoral', TRUE),

    (5, 'employee', TRUE),
    (5, 'undergraduate', TRUE),
    (5, 'master', TRUE),
    (5, 'doctoral', TRUE),

    (6, 'employee', FALSE),
    (6, 'undergraduate', FALSE),
    (6, 'master', FALSE),
    (6, 'doctoral', FALSE),

    (7, 'employee', FALSE),
    (7, 'undergraduate', FALSE),
    (7, 'master', FALSE),
    (7, 'doctoral', FALSE),

    (8, 'employee', FALSE),
    (8, 'undergraduate', FALSE),
    (8, 'master', FALSE),
    (8, 'doctoral', FALSE),

    (9, 'employee', FALSE),
    (9, 'undergraduate', FALSE),
    (9, 'master', FALSE),
    (9, 'doctoral', FALSE)

ON DUPLICATE KEY UPDATE
    is_allowed = VALUES(is_allowed);
