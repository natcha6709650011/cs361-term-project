(function () {
    const API_BASE_URL = "https://7i1mw8hw5l.execute-api.us-east-1.amazonaws.com/v1";
  
    // คอลัมน์ตามกลุ่มผู้ใช้ใน room_policies (teacher + staff รวมเป็น employee แล้ว)
    const COLUMNS = [
      { key: "undergraduate", label: "นักศึกษาปริญญาตรี" },
      { key: "master", label: "นักศึกษาปริญญาโท" },
      { key: "doctoral", label: "นักศึกษาปริญญาเอก" },
      { key: "employee", label: "อาจารย์/เจ้าหน้าที่" },
    ];
  
    const $ = (id) => document.getElementById(id);
    const rowsEl = $("permRows");
    const statusEl = $("permStatus");
    const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  
    const colCount = COLUMNS.length + 1;
    $("permHead").innerHTML = "<th>ประเภทห้อง</th>" + COLUMNS.map((c) => `<th class="c">${esc(c.label)}</th>`).join("");
  
    function showMessage(html) {
      rowsEl.innerHTML = `<tr><td colspan="${colCount}" class="admin-empty">${html}</td></tr>`;
    }
  
    async function getJson(path) {
      const res = await fetch(API_BASE_URL + path, { credentials: "include", headers: { Accept: "application/json" } });
      let data = null;
      try { data = await res.json(); } catch (e) {}
      if (res.status === 401) { window.location.href = "login.html"; throw new Error("กรุณาเข้าสู่ระบบใหม่"); }
      if (!res.ok) throw new Error((data && (data.message || data.error)) || "เกิดข้อผิดพลาด");
      return data;
    }
  
    const box = (allowed) => allowed === undefined
      ? '<span class="perm-box is-na" aria-label="ไม่มีข้อมูล">–</span>'
      : `<span class="perm-box${allowed ? " is-on" : ""}" role="img" aria-label="${allowed ? "จองได้" : "จองไม่ได้"}">${allowed ? '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="m3.5 8.5 3 3 6-7" /></svg>' : ""}</span>`;
  
    function render(roomTypes) {
      if (!roomTypes.length) return showMessage("ไม่พบข้อมูลประเภทห้อง");
      rowsEl.innerHTML = roomTypes.map((t) => {
        const map = {};
        (t.policies || []).forEach((p) => { map[p.user_type] = !!p.is_allowed; });
        return `<tr><td>${esc(t.type_name)}</td>${COLUMNS.map((c) => `<td class="c">${box(map[c.key])}</td>`).join("")}</tr>`;
      }).join("");
    }
  
    async function init() {
      if (localStorage.getItem("isLoggedIn") !== "true") {
        return showMessage('กรุณา<a href="login.html">เข้าสู่ระบบ</a>ด้วยบัญชีเจ้าหน้าที่ดูแลสถานที่ก่อน');
      }
      try {
        // สิทธิ์อ่านจากฐานข้อมูล เดียวกับที่ header ใช้แสดงเมนู "จัดการห้อง"
        const perm = await getJson("/me/permissions");
        if (!(perm && perm.user && perm.user.is_facility_admin === true)) {
          return showMessage("หน้านี้สำหรับเจ้าหน้าที่ดูแลสถานที่เท่านั้น");
        }
        const data = await getJson("/room-types");
        render(Array.isArray(data) ? data : data.room_types || []);
      } catch (e) {
        showMessage(esc(e.message));
      }
    }
  
    init();
  })();