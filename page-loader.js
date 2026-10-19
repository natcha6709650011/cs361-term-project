(function () {
  // สร้าง style สำหรับซ่อนหน้าเว็บระหว่างโหลด
  const style = document.createElement("style");

  style.textContent = `
    html:not(.page-loaded) body {
      visibility: hidden;
    }

    html:not(.page-loaded)::before {
      content: "กำลังโหลด...";
      position: fixed;
      inset: 0;
      z-index: 99999;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #fff;
      color: #b00020;
      font-size: 18px;
      font-weight: 600;
      visibility: visible;
    }

    html:not(.page-loaded)::after {
      content: "";
      position: fixed;
      top: 50%;
      left: 50%;
      width: 28px;
      height: 28px;
      margin: 30px 0 0 -14px;
      border: 3px solid #eee;
      border-top-color: #b00020;
      border-radius: 50%;
      animation: page-loader-spin 0.8s linear infinite;
      z-index: 100000;
      visibility: visible;
    }

    @keyframes page-loader-spin {
      to {
        transform: rotate(360deg);
      }
    }
  `;

  document.head.appendChild(style);

  // เมื่อหน้าโหลดเสร็จ ค่อยแสดงหน้าเว็บจริง
  window.addEventListener("load", function () {
    document.documentElement.classList.add("page-loaded");
  });
})();