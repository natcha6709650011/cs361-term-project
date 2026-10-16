-- =========================================
-- Mock Teacher
-- =========================================

-- อาจารย์ปกติ
INSERT INTO users (
    username,
    user_type,
    displayname_th,
    displayname_en,
    email,
    department,
    organization,
    employee_type,
    tu_status
)
VALUES (
    'teacher001',
    'employee',
    'อาจารย์ทดสอบ',
    'Test Teacher',
    'teacher001@tu.ac.th',
    'สาขาวิชาวิทยาการคอมพิวเตอร์',
    'คณะวิทยาศาสตร์และเทคโนโลยี',
    'teacher',
    'ปกติ'
);


-- อาจารย์ที่สามารถอนุมัติได้
INSERT INTO users (
    username,
    user_type,
    displayname_th,
    displayname_en,
    email,
    department,
    organization,
    employee_type,
    tu_status
)
VALUES (
    'teacher002',
    'employee',
    'อาจารย์ผู้อนุมัติ',
    'Test Approver',
    'teacher002@tu.ac.th',
    'สาขาวิชาวิทยาการคอมพิวเตอร์',
    'คณะวิทยาศาสตร์และเทคโนโลยี',
    'teacher',
    'ปกติ'
);


-- =========================================
-- Mock Staff
-- =========================================

-- เจ้าหน้าที่ปกติ
INSERT INTO users (
    username,
    user_type,
    displayname_th,
    displayname_en,
    email,
    department,
    organization,
    employee_type,
    tu_status
)
VALUES (
    'staff001',
    'employee',
    'เจ้าหน้าที่ทดสอบ',
    'Test Staff',
    'staff001@tu.ac.th',
    'งานบริการและจัดการห้อง',
    'คณะวิทยาศาสตร์และเทคโนโลยี',
    'staff',
    'ปกติ'
);


-- เจ้าหน้าที่ดูแลสถานที่
INSERT INTO users (
    username,
    user_type,
    displayname_th,
    displayname_en,
    email,
    department,
    organization,
    employee_type,
    tu_status
)
VALUES (
    'staff002',
    'employee',
    'เจ้าหน้าที่ดูแลสถานที่',
    'Test Facility Admin',
    'staff002@tu.ac.th',
    'งานบริการและจัดการห้อง',
    'คณะวิทยาศาสตร์และเทคโนโลยี',
    'staff',
    'ปกติ'
);


-- =========================================
-- Assign Special Roles
-- =========================================

-- teacher002 → APPROVER
INSERT INTO user_roles (
    user_id,
    role_id
)
SELECT
    u.user_id,
    r.role_id
FROM users AS u
JOIN roles AS r
    ON r.role_name = 'APPROVER'
WHERE u.username = 'teacher002';


-- staff002 → FACILITY_ADMIN
INSERT INTO user_roles (
    user_id,
    role_id
)
SELECT
    u.user_id,
    r.role_id
FROM users AS u
JOIN roles AS r
    ON r.role_name = 'FACILITY_ADMIN'
WHERE u.username = 'staff002';