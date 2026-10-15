const loginForm = document.getElementById('loginForm');
const loginError = document.getElementById('loginError');

loginForm.addEventListener('submit', function (event) {

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


  /*
    ตอนนี้ยังไม่ตรวจสอบกับ TU API

    ขั้นต่อไปจะเปลี่ยนส่วนนี้เป็น:

    Login Form
        ↓
    TU Authentication / TU API
        ↓
    ตรวจสอบสำเร็จ
        ↓
    ได้ข้อมูล User
        ↓
    เก็บ tuUser
        ↓
    index.html
  */


  // DEMO ชั่วคราว
  const demoUser = {
    username: username,
    displayname_th: username,
    displayname_en: username,
    type: "student"
  };


  localStorage.setItem(
    'tuUser',
    JSON.stringify(demoUser)
  );


  // กลับหน้าแรกหลัง Login
  window.location.href = 'index.html';

});