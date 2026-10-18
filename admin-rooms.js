(function () {
    const ROOMS_LIST_URL = "https://7i1mw8hw5l.execute-api.us-east-1.amazonaws.com/v1/rooms";
    const MANAGE_BASE_URL = "https://7i1mw8hw5l.execute-api.us-east-1.amazonaws.com"; // PATCH /rooms/{id}[/status]
  
    const $ = (id) => document.getElementById(id);
    const rowsEl = $("roomRows"), statusEl = $("adminStatus"), modal = $("roomModal"), menu = $("rowMenu");
    let rooms = [], current = null, mode = "view", menuRoom = null;
  
    const token = localStorage.getItem("authToken");
    let user = null;
    try { user = JSON.parse(localStorage.getItem("tuUser")); } catch (e) {}

    const isAdmin = !!token && !!user && String(user.role || "").toLowerCase() === "facility_admin";
  
    const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
    const onOff = (v) => `<span class="${v ? "on" : "off"}">${v ? "เปิด" : "ปิด"}</span>`;
    const amenities = (v) => { if (Array.isArray(v)) return v; try { return JSON.parse(v) || []; } catch (e) { return []; } };
  
    function notify(msg, isError) {
      statusEl.textContent = msg; statusEl.classList.toggle("is-error", !!isError); statusEl.hidden = false;
      clearTimeout(notify.t); if (!isError) notify.t = setTimeout(() => (statusEl.hidden = true), 3500);
    }
  
    async function api(url, options = {}) {
      const res = await fetch(url, { ...options, headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` } });
      let data = null; try { data = await res.json(); } catch (e) {}
      if (res.status === 401) { window.location.href = "login.html"; throw new Error("กรุณาเข้าสู่ระบบใหม่"); }
      if (res.status === 403) throw new Error("คุณไม่มีสิทธิ์จัดการห้อง");
      if (!res.ok) throw new Error((data && (data.message || data.error)) || "เกิดข้อผิดพลาด");
      return data;
    }
  
    function fillFilters() {
      const fill = (id, vals, label) => {
        const sel = $(id), keep = sel.value;
        sel.innerHTML = `<option value="">${label}</option>` + vals.map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join("");
        sel.value = vals.map(String).includes(keep) ? keep : "";
      };
      fill("fType", ["ห้องเรียน", "ห้องประชุม", "ห้องกิจกรรม", "ห้องปฏิบัติการ", "Co-Working Space"], "ประเภทห้อง");
      fill("fFloor", [...new Set([1, 2, 3, ...rooms.map((r) => r.floor).filter((f) => f != null)])].sort((a, b) => a - b), "ชั้น");
    }
  
    function render() {
      const q = $("fSearch").value.trim(), t = $("fType").value, f = $("fFloor").value;
      const list = rooms.filter((r) => (!q || String(r.room_number).includes(q)) && (!t || String(r.room_type || "").toLowerCase().includes(t.toLowerCase())) && (!f || String(r.floor) === f));
      rowsEl.innerHTML = list.length ? list.map((r) => `
        <tr data-id="${r.room_id}">
          <td>${esc(r.room_number)}</td><td>${esc(r.room_type)}</td>
          <td class="c">${r.capacity ?? "-"}</td><td class="c">${esc(r.floor)}</td>
          <td class="c">${onOff(r.is_active)}</td><td class="c">${onOff(r.is_bookable)}</td>
          <td class="c"><button type="button" class="dots" data-dots aria-label="เมนูห้อง ${esc(r.room_number)}" aria-haspopup="true">•••</button></td>
        </tr>`).join("") : '<tr><td colspan="7" class="admin-empty">ไม่พบห้องที่ตรงกับเงื่อนไข</td></tr>';
    }
  
    async function loadRooms() {
      try {
        const data = await api(ROOMS_LIST_URL);
        rooms = Array.isArray(data) ? data : data.rooms || [];
        fillFilters(); render();
      } catch (e) { rowsEl.innerHTML = `<tr><td colspan="7" class="admin-empty">${esc(e.message)}</td></tr>`; }
    }
    ["input", "change"].forEach((ev) => document.querySelector(".admin-filters").addEventListener(ev, render));
  
    const closeMenu = () => { menu.hidden = true; menuRoom = null; };
    rowsEl.addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-dots]"); if (!btn) return;
      ev.stopPropagation();
      if (!menu.hidden && menuRoom && String(menuRoom.room_id) === btn.closest("tr").dataset.id) return closeMenu();
      menuRoom = rooms.find((r) => String(r.room_id) === btn.closest("tr").dataset.id);
      const rect = btn.getBoundingClientRect();
      menu.hidden = false;
      menu.style.top = rect.bottom + 4 + "px";
      menu.style.left = Math.max(8, rect.right - menu.offsetWidth) + "px";
    });
    menu.addEventListener("click", (ev) => {
      const act = ev.target.closest("[data-act]")?.dataset.act; if (!act || !menuRoom) return;
      const room = menuRoom; closeMenu(); openModal(room, act === "edit" ? "edit" : "view");
    });
    document.addEventListener("click", closeMenu);
    window.addEventListener("scroll", closeMenu, true); window.addEventListener("resize", closeMenu);
  
    function openModal(room, m) { current = room; mode = m; draw(); modal.hidden = false; }
    const closeModal = () => { modal.hidden = true; current = null; };
  
    function draw(notice, isError) {
      const r = current, n = $("mNotice");
      $("mTitle").textContent = mode === "edit" ? `แก้ไขห้อง ${r.room_number}` : `ห้อง ${r.room_number}`;
      n.textContent = notice || ""; n.hidden = !notice; n.classList.toggle("is-error", !!isError);
      const items = amenities(r.amenities_json).map((a) => a.item).filter(Boolean);
  
      if (mode === "view") {
        $("mBody").innerHTML = `
          ${r.image_url ? `<img class="detail-img" src="${esc(r.image_url)}" alt="ห้อง ${esc(r.room_number)}" />` : ""}
          <dl class="detail">
            <dt>ห้อง</dt><dd>${esc(r.room_number)}</dd>
            <dt>ประเภทห้อง</dt><dd>${esc(r.room_type) || "-"}</dd>
            <dt>ชั้น</dt><dd>${esc(r.floor) || "-"}</dd>
            <dt>ความจุ</dt><dd>${r.capacity != null ? r.capacity + " คน" : "-"}</dd>
            <dt>เปิดใช้งาน</dt><dd>${onOff(r.is_active)}</dd>
            <dt>เปิดให้จอง</dt><dd>${onOff(r.is_bookable)}</dd>
            <dt>ผู้ดูแลห้อง</dt><dd>${esc(r.caretaker_name) || "-"}</dd>
            <dt>อุปกรณ์</dt><dd>${items.length ? `<span class="chips">${items.map((i) => `<span class="chip">${esc(i)}</span>`).join("")}</span>` : "-"}</dd>
          </dl>`;
        $("mActions").innerHTML = '<button type="button" class="btn btn--ghost" data-act="close">ปิด</button><button type="button" class="btn btn--primary" data-act="edit">แก้ไข</button>';
      } else {
        $("mBody").innerHTML = `
          <dl class="detail">
            <dt>ห้อง</dt><dd>${esc(r.room_number)}</dd>
            <dt>ประเภทห้อง</dt><dd>${esc(r.room_type) || "-"}</dd>
            <dt>เปิดใช้งาน</dt><dd>${onOff(r.is_active)}</dd>
          </dl>
          <label class="switch"><input type="checkbox" id="fBookable" ${r.is_bookable ? "checked" : ""} /><span class="switch__track"></span>เปิดให้จอง</label>
          <label>ความจุ (คน)<input type="number" id="fCapacity" min="1" step="1" value="${esc(r.capacity)}" placeholder="ไม่ระบุ" /></label>
          <label>ชั้น *<input type="number" id="fFloor" min="1" step="1" value="${esc(r.floor)}" required /></label>
          <label>ผู้ดูแลห้อง<input type="text" id="fCaretaker" maxlength="100" value="${esc(r.caretaker_name)}" /></label>
          <label>URL รูปภาพ<input type="url" id="fImage" maxlength="500" value="${esc(r.image_url)}" placeholder="https://..." /></label>
          <label>อุปกรณ์และสิ่งอำนวยความสะดวก<input type="text" id="fAmenities" value="${esc(items.join(", "))}" placeholder="โต๊ะ, เก้าอี้, ทีวี" /><small>คั่นแต่ละรายการด้วยเครื่องหมายจุลภาค (,)</small></label>`;
        $("mActions").innerHTML = '<button type="button" class="btn btn--ghost" data-act="cancel">ยกเลิก</button><button type="button" class="btn btn--primary" data-act="save" id="saveBtn">บันทึก</button>';
      }
    }
  
    async function save() {
      const cap = $("fCapacity").value.trim(), floor = $("fFloor").value.trim();
      const bad = [];
      if (cap && !(Number.isInteger(+cap) && +cap > 0)) bad.push("fCapacity");
      if (!(Number.isInteger(+floor) && +floor > 0)) bad.push("fFloor");
      ["fCapacity", "fFloor"].forEach((id) => $(id).classList.toggle("is-invalid", bad.includes(id)));
      if (bad.length) return draw2("กรุณากรอกความจุและชั้นเป็นจำนวนเต็มบวก", true);
  
      const body = {
        capacity: cap ? +cap : null, floor: +floor,
        caretaker_name: $("fCaretaker").value.trim() || null,
        image_url: $("fImage").value.trim() || null,
        amenities_json: $("fAmenities").value.split(",").map((s) => s.trim()).filter(Boolean).map((item) => ({ item })),
      };
      const bookable = $("fBookable").checked, btn = $("saveBtn");
      btn.disabled = true;
      try {
        const d = await api(`${MANAGE_BASE_URL}/rooms/${current.room_id}`, { method: "PATCH", body: JSON.stringify(body) });
        Object.assign(current, d && d.room ? d.room : body);
        if (!!current.is_bookable !== bookable) {
          await api(`${MANAGE_BASE_URL}/rooms/${current.room_id}/status`, { method: "PATCH", body: JSON.stringify({ is_bookable: bookable }) });
          current.is_bookable = bookable ? 1 : 0;
        }
        render(); fillFilters();
        mode = "view"; draw("บันทึกข้อมูลแล้ว กรุณาตรวจสอบความถูกต้อง");
      } catch (e) {
        render(); btn.disabled = false; draw2(e.message, true);
      }
    }
    // show a message without redrawing (keeps the user's input)
    function draw2(msg, isError) { const n = $("mNotice"); n.textContent = msg; n.hidden = false; n.classList.toggle("is-error", !!isError); }
  
    modal.addEventListener("click", (ev) => {
      const act = ev.target.closest("[data-act]")?.dataset.act; if (!act) return;
      if (act === "close") closeModal();
      else if (act === "edit") { mode = "edit"; draw(); }
      else if (act === "cancel") { mode = "view"; draw(); }
      else if (act === "save") save();
    });
    document.addEventListener("keydown", (ev) => {
      if (ev.key !== "Escape") return;
      if (!menu.hidden) closeMenu(); else if (!modal.hidden) closeModal();
    });
  
    fillFilters();
    if (!token || !user) {
      rowsEl.innerHTML = '<tr><td colspan="7" class="admin-empty">กรุณา<a href="login.html">เข้าสู่ระบบ</a>ด้วยบัญชีเจ้าหน้าที่ดูแลสถานที่ (facility_admin) ก่อน</td></tr>';
    } else if (!isAdmin) {
      rowsEl.innerHTML = '<tr><td colspan="7" class="admin-empty">หน้านี้สำหรับเจ้าหน้าที่ดูแลสถานที่เท่านั้น (บัญชีนี้ role: ' + esc(user.role || "-") + ')</td></tr>';
    } else {
      loadRooms();
    }
  })();