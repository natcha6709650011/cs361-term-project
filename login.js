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

    // Login สำเร็จ
    // เก็บข้อมูล User ที่ได้จาก TU API
    localStorage.setItem(
      'tuUser',
      JSON.stringify(data)
    );

    console.log('Login successful:', data);

    // กลับหน้าแรกหลัง Login
    window.location.href = 'index.html';

  } catch (error) {

    console.error('Login error:', error);

    loginError.textContent =
      'ไม่สามารถเชื่อมต่อระบบ Login ได้';

    loginError.style.display = 'block';
  }

});