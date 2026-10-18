const loginForm = document.getElementById('loginForm');
const loginError = document.getElementById('loginError');
const API_BASE_URL = window.location.port === '5501'
    ? '/api/v1'
    : 'https://7i1mw8hw5l.execute-api.us-east-1.amazonaws.com/v1';
const LOGIN_API_URL = `${API_BASE_URL}/auth/login`;

loginForm.addEventListener('submit', async function (event) {

    event.preventDefault();

    const username =
        document.getElementById('username').value.trim();

    const password =
        document.getElementById('password').value;

    // ตรวจสอบข้อมูล
    if (!username || !password) {

        loginError.textContent =
            'กรุณากรอก username และ password';

        loginError.style.display = 'block';

        return;
    }

    // ซ่อน error เดิม
    loginError.style.display = 'none';

    try {

        console.log('Sending login request:', {
            username: username
        });

        const response = await fetch(
            LOGIN_API_URL,
            {
                method: 'POST',

                headers: {
                    'Content-Type': 'application/json'
                },

                body: JSON.stringify({
                    username: username,
                    password: password
                })
            }
        );

        const data = await response.json();

        console.log('API Status:', response.status);
        console.log('API Response:', data);

        // Login ไม่สำเร็จ
        if (!response.ok || !data.status) {

            loginError.textContent =
                data.message ||
                'Username หรือ Password ไม่ถูกต้อง';

            loginError.style.display = 'block';

            return;
        }

        // ==========================================
        // ตรวจสอบว่ามี JWT กลับมาจริง
        // ==========================================

        if (!data.token) {

            console.error(
                'Login succeeded but token is missing:',
                data
            );

            loginError.textContent =
                'เข้าสู่ระบบสำเร็จ แต่ระบบไม่ได้รับ Token';

            loginError.style.display = 'block';

            return;
        }

        // ==========================================
        // Login สำเร็จ
        // ==========================================

        const user = data.user || {};

        // JWT ที่ Lambda ของเราออกเอง
        localStorage.setItem(
            'authToken',
            data.token
        );

        // ข้อมูล User
        localStorage.setItem(
            'tuUser',
            JSON.stringify(user)
        );

        // Username
        localStorage.setItem(
            'username',
            user.username || username
        );

        // สถานะ Login
        localStorage.setItem(
            'isLoggedIn',
            'true'
        );

        // ==========================================
        // Debug
        // ==========================================

        console.log(
            'JWT received:',
            data.token
        );

        console.log(
            'User:',
            user
        );

        console.log(
            'Saved authToken:',
            localStorage.getItem('authToken')
        );

        console.log(
            'Saved tuUser:',
            localStorage.getItem('tuUser')
        );

        // ==========================================
        // ไปหน้าแรก
        // ==========================================

        window.location.href = 'index.html';

    } catch (error) {

        console.error(
            'Login error:',
            error
        );

        loginError.textContent =
            'ไม่สามารถเชื่อมต่อระบบ Login ได้';

        loginError.style.display = 'block';
    }

});
