(function () {
  const API_BASE_URL = "/api";

  const COLUMNS = [
    { key: "undergraduate", label: "นักศึกษาปริญญาตรี" },
    { key: "master", label: "นักศึกษาปริญญาโท" },
    { key: "doctoral", label: "นักศึกษาปริญญาเอก" },
    { key: "employee", label: "อาจารย์/เจ้าหน้าที่" },
  ];

  const $ = (id) => document.getElementById(id);
  const rowsEl = $("permRows");
  const statusEl = $("permStatus");
  const saveBtn = $("permSave");
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const colCount = COLUMNS.length + 1;
  let original = {};
  let saving = false;

  $("permHead").innerHTML = "<th>ประเภทห้อง</th>" + COLUMNS.map((c) => `<th class="c">${esc(c.label)}</th>`).join("");

  function notify(msg, isError) {
    statusEl.textContent = msg;
    statusEl.classList.toggle("is-error", !!isError);
    statusEl.hidden = !msg;
  }

  function showMessage(html) {
    rowsEl.innerHTML = `<tr><td colspan="${colCount}" class="admin-empty">${html}</td></tr>`;
  }

  async function request(path, options = {}) {
    const res = await fetch(API_BASE_URL + path, {
      credentials: "include",
      ...options,
      headers: { Accept: "application/json", ...(options.body ? { "Content-Type": "application/json" } : {}) },
    });
    let data = null;
    try { data = await res.json(); } catch (e) {}
    if (res.status === 401) { window.location.href = "login.html"; throw new Error("กรุณาเข้าสู่ระบบใหม่"); }
    if (res.status === 403) throw new Error("คุณไม่มีสิทธิ์แก้ไขสิทธิ์การจองห้อง");
    if (!res.ok) throw new Error((data && (data.message || data.error)) || "เกิดข้อผิดพลาด");
    return data;
  }

  const keyOf = (typeId, userType) => `${typeId}|${userType}`;

  function render(roomTypes) {
    if (!roomTypes.length) return showMessage("ไม่พบข้อมูลประเภทห้อง");
    original = {};
    rowsEl.innerHTML = roomTypes.map((t) => {
      (t.policies || []).forEach((p) => { original[keyOf(t.room_type_id, p.user_type)] = !!p.is_allowed; });
      const cells = COLUMNS.map((c) => {
        const k = keyOf(t.room_type_id, c.key);
        return `<td class="c"><input type="checkbox" class="perm-check" data-type="${esc(t.room_type_id)}" data-user="${esc(c.key)}" ${original[k] ? "checked" : ""} aria-label="${esc(t.type_name)} — ${esc(c.label)}" /></td>`;
      }).join("");
      return `<tr><td>${esc(t.type_name)}</td>${cells}</tr>`;
    }).join("");
    refreshState();
  }

  function collectChanges() {
    const changes = [];
    rowsEl.querySelectorAll(".perm-check").forEach((box) => {
      const typeId = Number(box.dataset.type);
      const was = original[keyOf(typeId, box.dataset.user)] === true;
      const td = box.closest("td");
      const changed = box.checked !== was;
      td.classList.toggle("is-changed", changed);
      if (changed) changes.push({ room_type_id: typeId, user_type: box.dataset.user, is_allowed: box.checked });
    });
    return changes;
  }

  function refreshState() {
    const n = collectChanges().length;
    saveBtn.disabled = saving || n === 0;
    saveBtn.textContent = saving ? "กำลังบันทึก..." : n ? `บันทึกการเปลี่ยนแปลง (${n})` : "บันทึกการเปลี่ยนแปลง";
  }

  async function load() {
    const data = await request("/room-types");
    render(Array.isArray(data) ? data : data.room_types || []);
  }

  rowsEl.addEventListener("change", (ev) => {
    if (!ev.target.classList.contains("perm-check")) return;
    notify("");
    refreshState();
  });

  saveBtn.addEventListener("click", async () => {
    const changes = collectChanges();
    if (!changes.length || saving) return;
    saving = true; refreshState(); notify("");
    try {
      await request("/room-policies", { method: "PUT", body: JSON.stringify({ changes }) });
      saving = false;
      await load(); // โหลดจากเซิร์ฟเวอร์ใหม่ เพื่อให้เห็นว่าบันทึกถูกต้องจริง
      notify("บันทึกสิทธิ์การจองห้องแล้ว กรุณาตรวจสอบความถูกต้อง", false);
    } catch (e) {
      saving = false; refreshState();
      notify(e.message, true);
    }
  });

  window.addEventListener("beforeunload", (ev) => {
    if (!saving && collectChanges().length) { ev.preventDefault(); ev.returnValue = ""; }
  });

  async function init() {
    if (localStorage.getItem("isLoggedIn") !== "true") {
      return showMessage('กรุณา<a href="login.html">เข้าสู่ระบบ</a>ด้วยบัญชีเจ้าหน้าที่ดูแลสถานที่ก่อน');
    }
    try {
      const perm = await request("/me/permissions");
      if (!(perm && perm.user && perm.user.is_facility_admin === true)) {
        saveBtn.hidden = true;
        return showMessage("หน้านี้สำหรับเจ้าหน้าที่ดูแลสถานที่เท่านั้น");
      }
      await load();
    } catch (e) {
      showMessage(esc(e.message));
    }
  }

  init();
})();