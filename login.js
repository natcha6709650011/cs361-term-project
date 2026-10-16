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

    console.log('Sending to TU API:', {
      username: username
    });

    const response = await fetch(
      'https://restapi.tu.ac.th/api/v1/auth/Ad/verify',
      {
        method: 'POST',

        headers: {
          'Content-Type': 'application/json',
          'Application-Key': 'TU8acabf0056d3dca25afa2c93086ef46b0e3c309eb19b09123e47d2c1032ee24247c3369bf04516431c1eec63907a8bcb'
        },

        body: JSON.stringify({
          UserName: username,
          PassWord: password
        })
      }
    );

    const data = await response.json();

    console.log('TU API Status:', response.status);
    console.log('TU API Response:', data);

    // Login ไม่สำเร็จ
    if (!response.ok || !data.status) {

      loginError.textContent =
        'Username หรือ Password ไม่ถูกต้อง';

      loginError.style.display = 'block';

      return;
    }

    // ==========================================
    // Login สำเร็จ
    // ==========================================

    // เก็บข้อมูล User ทั้งหมดที่ได้จาก TU API
    localStorage.setItem(
      'tuUser',
      JSON.stringify(data)
    );

    // เก็บ username แยกไว้ด้วย
    localStorage.setItem(
      'username',
      username
    );

    // แสดงข้อมูลที่ถูกเก็บไว้ใน Console
    console.log('Login successful:', data);
    console.log(
      'Saved tuUser:',
      localStorage.getItem('tuUser')
    );

    console.log(
      'Saved username:',
      localStorage.getItem('username')
    );

    // ==========================================
    // เตรียมข้อมูลสำหรับ Permission
    // ==========================================
    // ตอนนี้ยังไม่เดาว่า TU API ใช้ field ไหน
    // สำหรับแยก ตรี / โท / เอก
    // เก็บข้อมูลจริงจาก API ไว้ก่อน
    // แล้ว Permission จะอ่านจาก tuUser ภายหลัง
    // ==========================================

    localStorage.setItem(
      'isLoggedIn',
      'true'
    );

    // กลับหน้าแรกหลัง Login
    window.location.href = 'index.html';

  } catch (error) {

    console.error('Login error:', error);

    loginError.textContent =
      'ไม่สามารถเชื่อมต่อระบบ Login ได้';

    loginError.style.display = 'block';
  }

});