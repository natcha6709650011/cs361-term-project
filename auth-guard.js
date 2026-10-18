// ======================================================
// CSTU Room Booking
// Authentication & Authorization Guard
// ======================================================


// ======================================================
// 1. GET CURRENT USER
// ======================================================

function getCurrentUser() {
    const storedUser = localStorage.getItem("tuUser");

    if (!storedUser) {
        return null;
    }

    try {
        return JSON.parse(storedUser);
    } catch (error) {
        console.error("Invalid tuUser data:", error);

        localStorage.removeItem("tuUser");

        return null;
    }
}


// ======================================================
// 2. LOGIN CHECK
// ======================================================

function isLoggedIn() {
    return getCurrentUser() !== null;
}


function requireLogin() {
    const user = getCurrentUser();

    if (!user) {
        alert("กรุณาเข้าสู่ระบบก่อน");
        window.location.href = "login.html";
        return null;
    }

    return user;
}


// ======================================================
// 3. GET ROLE
// ======================================================

function getUserRole() {
    const user = getCurrentUser();

    if (!user) {
        return null;
    }

    // อาจารย์ผู้อนุมัติ
    if (user.role === "teacher" && user.username === "teacher002") {
        return "approver";
    }

    // อาจารย์ธรรมดา + เจ้าหน้าที่ปกติ = employee
    if (user.user_type === "employee") {
        return "employee";
    }

    return user.role || user.user_type || null;
}


// ======================================================
// 4. GET STUDENT LEVEL
// ======================================================
// รองรับข้อมูลที่อาจใช้ชื่อ field ต่างกัน
//
// undergraduate = ปริญญาตรี
// master        = ปริญญาโท
// doctoral      = ปริญญาเอก
//
// สำคัญ:
// auth-guard ไม่ได้ตัดสินว่า student จองห้องไหนได้
// เรื่องนั้นให้ database policy เป็นตัวตัดสิน
// ======================================================

function getStudentLevel() {
    const user = getCurrentUser();

    if (!user) {
        return null;
    }

    return (
        user.level ||
        user.education_level ||
        user.program_type ||
        user.student_level ||
        null
    );
}

// ======================================================
// 5. BASIC ROLE CHECKS
// ======================================================

function hasRole(requiredRole) {
    return getUserRole() === requiredRole;
}


function hasAnyRole(requiredRoles) {
    return requiredRoles.includes(getUserRole());
}


// ======================================================
// 6. STUDENT CHECKS
// ======================================================

function isStudent() {
    return hasRole("student");
}


function isMaster() {
    return isStudent() && getStudentLevel() === "master";
}


function isDoctoral() {
    return isStudent() && getStudentLevel() === "doctoral";
}

// ======================================================
// 7. EMPLOYEE / SPECIAL ROLE CHECKS
// ======================================================

function isEmployee() {
    return getUserRole() === "employee";
}

function isApprover() {
    return getUserRole() === "approver";
}


function isFacilityAdmin() {
    return hasRole("facility_admin");
}


// ======================================================
// 8. BOOKING PERMISSIONS
// ======================================================
// ทุก role ที่ login แล้วสามารถเข้าหน้าจองได้
//
// แต่สิทธิ์ว่า "จองห้องประเภทไหนได้"
// ให้ backend / database policy เป็นตัวตัดสิน
//
// ตัวอย่าง DB policy:
// student + room_type + is_allowed
// employee + room_type + is_allowed
// ======================================================

function canBookRoom() {
    const user = getCurrentUser();

    if (!user) {
        return false;
    }

    return [
        "student",
        "employee",
        "approver",
        "facility_admin"
    ].includes(getUserRole());
}


function requireBookingAccess() {
    const user = requireLogin();

    if (!user) {
        return null;
    }

    if (!canBookRoom()) {
        alert("คุณไม่มีสิทธิ์จองห้อง");
        window.location.href = "index.html";
        return null;
    }

    return user;
}


// ======================================================
// 9. MY BOOKINGS
// ======================================================
// ทุกคนที่ login แล้วดูการจองของตัวเองได้
// ======================================================

function canViewMyBookings() {
    return isLoggedIn();
}


function requireMyBookingsAccess() {
    return requireLogin();
}


// ======================================================
// 10. APPROVAL PERMISSION
// ======================================================
// เฉพาะ "อาจารย์อนุมัติ"
// facility_admin ไม่ใช่ approver
// ======================================================

function canApproveBooking() {
    return isApprover();
}


function requireApprover() {
    return requireRole("approver");
}


// ======================================================
// 11. ROOM MANAGEMENT PERMISSION
// ======================================================
// เฉพาะเจ้าหน้าที่สถานที่
// ======================================================

function canManageRoom() {
    return isFacilityAdmin();
}


function requireFacilityAdmin() {
    return requireRole("facility_admin");
}


// ======================================================
// 12. REQUIRE EXACT ROLE
// ======================================================

function requireRole(requiredRole) {
    const user = requireLogin();

    if (!user) {
        return null;
    }

    if (getUserRole() !== requiredRole) {
        alert("คุณไม่มีสิทธิ์เข้าถึงหน้านี้");
        window.location.href = "index.html";
        return null;
    }

    return user;
}


// ======================================================
// 13. REQUIRE ONE OF MULTIPLE ROLES
// ======================================================

function requireAnyRole(requiredRoles) {
    const user = requireLogin();

    if (!user) {
        return null;
    }

    if (!requiredRoles.includes(getUserRole())) {
        alert("คุณไม่มีสิทธิ์เข้าถึงหน้านี้");
        window.location.href = "index.html";
        return null;
    }

    return user;
}


// ======================================================
// 14. ROLE-BASED MENU
// ======================================================
//
// HTML สามารถเขียน:
//
// <a href="approval.html"
//    data-role="approver">
//    อนุมัติการจอง
// </a>
//
// <a href="manage-room.html"
//    data-role="facility_admin">
//    จัดการห้อง
// </a>
//
// หรือ:
//
// <a href="booking.html"
//    data-require-login>
//    จองห้อง
// </a>
// ======================================================

function updateRoleBasedMenu() {
    const user = getCurrentUser();
    const role = getUserRole();

    // ----------------------------------------------
    // Elements ที่ต้องการ role เดียว
    // ----------------------------------------------

    const roleElements = document.querySelectorAll("[data-role]");

    roleElements.forEach((element) => {
        const requiredRole = element.dataset.role;

        if (!user || role !== requiredRole) {
            element.style.display = "none";
        } else {
            element.style.display = "";
        }
    });


    // ----------------------------------------------
    // Elements ที่อนุญาตหลาย role
    // ----------------------------------------------

    const multiRoleElements =
        document.querySelectorAll("[data-roles]");

    multiRoleElements.forEach((element) => {
        const allowedRoles = element.dataset.roles
            .split(",")
            .map((role) => role.trim());

        if (!user || !allowedRoles.includes(role)) {
            element.style.display = "none";
        } else {
            element.style.display = "";
        }
    });


    // ----------------------------------------------
    // Elements ที่ต้อง login
    // ----------------------------------------------

    const loginRequiredElements =
        document.querySelectorAll("[data-require-login]");

    loginRequiredElements.forEach((element) => {
        if (!user) {
            element.style.display = "none";
        } else {
            element.style.display = "";
        }
    });


    // ----------------------------------------------
    // Elements สำหรับคนที่ยังไม่ได้ login
    // ----------------------------------------------

    const guestOnlyElements =
        document.querySelectorAll("[data-guest-only]");

    guestOnlyElements.forEach((element) => {
        if (user) {
            element.style.display = "none";
        } else {
            element.style.display = "";
        }
    });
}


// ======================================================
// 15. RUN MENU CHECK AUTOMATICALLY
// ======================================================

document.addEventListener("DOMContentLoaded", () => {
    updateRoleBasedMenu();
});