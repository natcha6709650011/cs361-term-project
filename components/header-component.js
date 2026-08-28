(() => {
  const componentScript = document.currentScript;
  const componentDirectory = new URL('./', componentScript.src);
  const stylesheet = document.createElement('link');
  stylesheet.rel = 'stylesheet';
  stylesheet.href = new URL('header.css', componentDirectory);
  document.head.appendChild(stylesheet);

  let target = document.querySelector('[data-site-header]');
  if (!target) {
    target = document.createElement('div');
    target.dataset.siteHeader = '';
    document.body.prepend(target);
  }

  target.innerHTML = `
    <header class="site-header">
      <a class="brand" href="index.html" aria-label="Computer Science Thammasat University">
        <img src="assets/cstu-logo.png" alt="Computer Science Thammasat University" />
        <span class="brand-divider" aria-hidden="true"></span>
        <span class="brand-name"><b>CS</b><span>COMPUTER SCIENCE<br />THAMMASAT UNIVERSITY</span></span>
      </a>
      <button class="menu-toggle" aria-label="เปิดเมนู" aria-expanded="false">☰</button>
      <nav class="main-nav" aria-label="เมนูหลัก">
        <a href="index.html">หน้าหลัก</a>
        <div class="nav-dropdown">
          <button class="dropdown-toggle" type="button" aria-expanded="false" aria-controls="room-type-menu">ประเภทห้อง <svg aria-hidden="true" viewBox="0 0 16 10"><path d="m2 2 6 6 6-6" /></svg></button>
          <div class="dropdown-menu" id="room-type-menu">
            <a href="room-types.html?type=classroom">ห้องเรียน</a>
            <a href="room-types.html?type=meeting">ห้องประชุม</a>
            <a href="room-types.html?type=activity">ห้องกิจกรรม</a>
            <a href="room-types.html?type=lab">ห้องปฏิบัติการ</a>
            <a href="room-types.html?type=coworking">Co-Working Space</a>
          </div>
        </div>
        <a href="guidelines.html">ข้อปฏิบัติ</a>
        <a href="contact.html">ติดต่อเรา</a>
        <a class="user-link" href="profile.html"><span class="user-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="3.5"/><path d="M4.5 20c.5-4 3.1-6 7.5-6s7 2 7.5 6"/></svg></span> Xxxxxxxxx.x</a>
      </nav>
    </header>`;

  const header = target.querySelector('.site-header');
  const menuButton = header.querySelector('.menu-toggle');
  const navigation = header.querySelector('.main-nav');
  const dropdown = header.querySelector('.nav-dropdown');
  const dropdownButton = header.querySelector('.dropdown-toggle');

  // ทำสีแดงให้เมนูของหน้าที่กำลังเปิดอยู่โดยอัตโนมัติ
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  const activeLink = header.querySelector(`.main-nav a[href="${currentPage}"]`);
  if (activeLink) activeLink.classList.add('active');
  if (currentPage === 'room-types.html') dropdownButton.classList.add('active');

  menuButton.addEventListener('click', () => {
    const isOpen = navigation.classList.toggle('open');
    menuButton.setAttribute('aria-expanded', String(isOpen));
    menuButton.setAttribute('aria-label', isOpen ? 'ปิดเมนู' : 'เปิดเมนู');
  });
  dropdownButton.addEventListener('click', () => {
    const isOpen = dropdown.classList.toggle('open');
    dropdownButton.setAttribute('aria-expanded', String(isOpen));
  });
  document.addEventListener('click', (event) => {
    if (!dropdown.contains(event.target)) {
      dropdown.classList.remove('open');
      dropdownButton.setAttribute('aria-expanded', 'false');
    }
  });
})();
