CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,

    username VARCHAR(50) NOT NULL UNIQUE,

    user_type ENUM(
        'student',
        'employee'
    ) NOT NULL,

    displayname_th VARCHAR(255),
    displayname_en VARCHAR(255),

    email VARCHAR(255),

    faculty VARCHAR(255),
    program VARCHAR(255),

    education_level ENUM(
        'undergraduate',
        'master',
        'doctoral'
    ),

    program_type ENUM(
        'regular',
        'special'
    ),

    year_level INT,

    department VARCHAR(255),
    organization VARCHAR(255),

    employee_type ENUM(
        'teacher',
        'staff'
    ),

    tu_status VARCHAR(50),
    status_id VARCHAR(20),
    status_work VARCHAR(20),
    status_emp VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);