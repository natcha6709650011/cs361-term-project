// ==========================================
// Authorization / Permission Control
// ==========================================

// ดึงข้อมูล User ที่ Login สำเร็จแล้ว
function getCurrentUser() {

    const userData = localStorage.getItem('tuUser');

    if (!userData) {
        return null;
    }

    try {
        return JSON.parse(userData);
    } catch (error) {

        console.error(
            'Cannot read user data:',
            error
        );

        return null;
    }
}


// ==========================================
// ตรวจสอบว่า Login แล้วหรือยัง
// ==========================================

function isUserLoggedIn() {

    const isLoggedIn =
        localStorage.getItem('isLoggedIn');

    const authToken =
        localStorage.getItem('authToken');

    const user =
        getCurrentUser();

    return (
        isLoggedIn === 'true' &&
        !!authToken &&
        !!user
    );
}


// ==========================================
// ตรวจสอบสิทธิ์ตามประเภทห้อง
// ==========================================

function hasRoomPermission(roomType) {

    const user = getCurrentUser();

    if (!user) {
        return false;
    }

    const userType =
        user.user_type || user.type;

    const educationLevel =
        user.education_level;

    const role =
        user.role;


    // ==========================================
    // FACILITY_ADMIN
    // เจ้าหน้าที่สถานที่ = ทุกห้อง
    // ==========================================

    if (role === 'FACILITY_ADMIN') {

        return true;
    }


    // ==========================================
    // APPROVER
    // สิทธิ์ใช้งานห้องเหมือนอาจารย์
    // ==========================================

    if (role === 'APPROVER') {

        if (
            roomType === 'classroom' ||
            roomType === 'computer_lab' ||
            roomType === 'meeting_room' ||
            roomType === 'student_activity'
        ) {

            return true;
        }

        return false;
    }


    // ==========================================
    // EMPLOYEE / TEACHER
    // ==========================================

    if (userType === 'employee') {

        if (
            roomType === 'classroom' ||
            roomType === 'computer_lab' ||
            roomType === 'meeting_room' ||
            roomType === 'student_activity'
        ) {

            return true;
        }

        return false;
    }


    // ==========================================
    // STUDENT
    // ==========================================

    if (userType === 'student') {


        // --------------------------------------
        // ปริญญาตรี
        // --------------------------------------

        if (
            educationLevel === 'undergraduate'
        ) {

            if (
                roomType === 'meeting_room' ||
                roomType === 'student_activity'
            ) {

                return true;
            }

            return false;
        }


        // --------------------------------------
        // ปริญญาโท
        // --------------------------------------

        if (
            educationLevel === 'master'
        ) {

            if (
                roomType === 'meeting_room' ||
                roomType === 'coworking' ||
                roomType === 'student_activity'
            ) {

                return true;
            }

            return false;
        }


        // --------------------------------------
        // ปริญญาเอก
        // --------------------------------------

        if (
            educationLevel === 'doctoral'
        ) {

            if (
                roomType === 'meeting_room' ||
                roomType === 'coworking' ||
                roomType === 'student_activity'
            ) {

                return true;
            }

            return false;
        }
    }


    // ==========================================
    // ไม่ตรงกับสิทธิ์ใด ๆ
    // ==========================================

    return false;
}


// ==========================================
// ตรวจสอบสิทธิ์ก่อนเข้าใช้งาน
// ==========================================

function checkRoomPermission(roomType) {

    // --------------------------------------
    // ยังไม่ได้ Login
    // --------------------------------------

    if (!isUserLoggedIn()) {

        alert(
            'กรุณาเข้าสู่ระบบก่อนจองห้อง'
        );

        window.location.href =
            'login.html';

        return false;
    }


    // --------------------------------------
    // Login แล้ว แต่ไม่มีสิทธิ์
    // --------------------------------------

    if (!hasRoomPermission(roomType)) {

        alert(
            'คุณไม่มีสิทธิ์เข้าถึงการจองห้องประเภทนี้'
        );

        return false;
    }


    // --------------------------------------
    // มีสิทธิ์
    // --------------------------------------

    return true;
}