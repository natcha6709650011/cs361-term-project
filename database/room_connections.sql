CREATE TABLE room_connections (
    connection_id INT AUTO_INCREMENT PRIMARY KEY,

    room_id_1 INT NOT NULL,
    room_id_2 INT NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_room_connections_room_1
        FOREIGN KEY (room_id_1)
        REFERENCES rooms(room_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_room_connections_room_2
        FOREIGN KEY (room_id_2)
        REFERENCES rooms(room_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_room_connection
        UNIQUE (room_id_1, room_id_2),

    CONSTRAINT chk_different_rooms
        CHECK (room_id_1 < room_id_2)
);

INSERT INTO room_connections
    (room_id_1, room_id_2)
VALUES
    (14, 15),
    (15, 16);