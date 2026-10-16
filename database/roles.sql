CREATE TABLE roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,

    role_name VARCHAR(50) NOT NULL UNIQUE,

    description VARCHAR(255)
);

INSERT INTO roles (
    role_name,
    description
)
VALUES
(
    'APPROVER',
    'สามารถอนุมัติคำขอจองห้อง'
),
(
    'FACILITY_ADMIN',
    'สามารถจัดการห้องและข้อมูลการใช้ห้อง'
);