const loginForm = document.getElementById('loginForm');
const loginError = document.getElementById('loginError');

loginForm.addEventListener('submit', async function (event) {

  event.preventDefault();

  const username =
    document.getElementById('username').value.trim();

  const password =
    document.getElementById('password').value.trim();

  // ตรวจสอบว่ากรอกข้อมูลครบหรือไม่
  if (!username || !password) {

    loginError.textContent =
      'กรุณากรอก username และ password';

    loginError.style.display = 'block';

    return;
  }

  try {

    console.log('Sending login request:', {
      username: username
    });

    // เรียก API Gateway ของระบบเรา
    const response = await fetch(
      'https://7i1mw8hw5l.execute-api.us-east-1.amazonaws.com/auth/login',
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
        data.message || 'Username หรือ Password ไม่ถูกต้อง';

      loginError.style.display = 'block';

      return;
    }

    // ==========================================
    // Login สำเร็จ
    // ==========================================

    const user = data.user;

    // เก็บ Authentication token
    localStorage.setItem(
      'authToken',
      data.token
    );

    // เก็บข้อมูล User ที่ Lambda ส่งกลับมา
    localStorage.setItem(
      'tuUser',
      JSON.stringify(user)
    );

    // เก็บ username
    localStorage.setItem(
      'username',
      user.username || username
    );

    // สถานะ Login
    localStorage.setItem(
      'isLoggedIn',
      'true'
    );

    console.log('Login successful:', data);

    console.log(
      'Saved tuUser:',
      localStorage.getItem('tuUser')
    );

    console.log(
      'Saved authToken:',
      localStorage.getItem('authToken')
    );

    // ==========================================
    // ไปหน้าแรก
    // ==========================================

    window.location.href = 'index.html';

  } catch (error) {

    console.error('Login error:', error);

    loginError.textContent =
      'ไม่สามารถเชื่อมต่อระบบ Login ได้';

    loginError.style.display = 'block';
  }

});