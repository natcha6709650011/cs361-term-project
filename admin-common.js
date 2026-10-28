/* =========================================================
   V3 Admin pages - ฟังก์ชันที่ใช้ร่วมกัน
   (approval.js, facility-schedule.js)

   CONFIG: แก้ REMOTE_API_URL / TOKEN_STORAGE_KEY ที่นี่ที่เดียว
   ========================================================= */

// รูปแบบเดียวกับ booking-api-config.js:
// เปิดผ่าน dev-server.js (port 5501) จะเรียกผ่าน proxy /api เพื่อเลี่ยง CORS
const REMOTE_API_URL =
  'https://7i1mw8hw5l.execute-api.us-east-1.amazonaws.com';

const API_BASE_URL =
  window.location.port === '5501' ? '/api' : REMOTE_API_URL;

const $ = (id) => document.getElementById(id);

/* ---------- Login guard ---------- */

// ถ้ายังไม่ได้ Login ให้ไปหน้า login.html
// (ตั้งชื่อ ensureLoggedIn เพื่อไม่ชนกับ requireLogin() ใน auth-guard.js)
// หมายเหตุ: เป็นแค่ความสะดวกของ UI สิทธิ์จริงตรวจที่ Backend ทุกครั้ง
function ensureLoggedIn() {
  const loggedIn = localStorage.getItem('isLoggedIn') === 'true';

  if (!loggedIn || !localStorage.getItem('tuUser')) {
    window.location.replace('login.html');
    return false;
  }

  return true;
}

/* ---------- API ---------- */

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    let message =
      data.message || data.error || `HTTP ${response.status}`;

    // API Gateway ตอบ 401/403 พร้อมข้อความสั้นๆ เมื่อ JWT authorizer ไม่ผ่าน
    // (token หมดอายุ / ไม่ถูกต้อง) ต่างจาก 403 ของ Lambda ที่เป็นเรื่อง Role
    if (response.status === 401 || message === 'Forbidden') {
      message =
        'Token หมดอายุ/ไม่ถูกต้อง หรือบัญชีนี้ไม่มีสิทธิ์ ' +
        'กรุณาเข้าสู่ระบบใหม่';
    }

    // กรณีคืนตารางแล้วชนกับการจอง
    const conflicts = data.details?.conflicting_bookings;

    if (conflicts) {
      const list = conflicts
        .map(
          (item) =>
            `#${item.booking_id} ${item.status} ` +
            `(${item.start_time}–${item.end_time})`
        )
        .join(', ');

      message += `\nรายการที่ชน: ${list}`;
    }

    throw new Error(message);
  }

  return data;
}

/* ---------- Permissions (จากตาราง user_roles ผ่าน /me/permissions) ---------- */

async function loadPermissions() {
  const data = await api('/v1/me/permissions');

  return data.user || {};
}

/**
 * เริ่มต้นหน้า: ตรวจ login, โหลด role จริงจาก Backend
 * - ซ่อนแท็บที่ผู้ใช้ไม่มีสิทธิ์ (ดู data-requires ใน HTML)
 * - ถ้าไม่มีสิทธิ์ของหน้านี้ จะซ่อนเนื้อหาและแจ้งเตือน
 * requiredFlag: 'is_approver' หรือ 'is_facility_admin'
 * คืนค่า true เมื่อควรโหลดข้อมูลของหน้าต่อ
 * (UI เป็นแค่ความสะดวก สิทธิ์จริงตรวจที่ Backend ทุกครั้ง)
 */
async function initAdminPage(requiredFlag) {
  if (!ensureLoggedIn()) return false;

  let user;

  try {
    user = await loadPermissions();
  } catch (error) {
    // ถ้าเช็ก role ไม่ได้ ให้ลองโหลดข้อมูลต่อ Backend จะปฏิเสธเองถ้าไม่มีสิทธิ์
    console.warn('โหลดสิทธิ์ผู้ใช้ไม่สำเร็จ:', error.message);
    return true;
  }

  document.querySelectorAll('[data-requires]').forEach((tab) => {
    tab.hidden = !user[tab.dataset.requires];
  });

  if (user[requiredFlag]) return true;

  const roleName =
    requiredFlag === 'is_approver' ? 'APPROVER' : 'FACILITY_ADMIN';

  document.querySelectorAll('main .panel').forEach((panel) => {
    panel.hidden = true;
  });

  setNotice(
    `หน้านี้สำหรับผู้ที่มี Role ${roleName} เท่านั้น ` +
      'บัญชีของคุณไม่มีสิทธิ์เข้าใช้งาน',
    'error'
  );

  return false;
}

/* ---------- UI helpers ---------- */

// type: '' | 'success' | 'error'
function setNotice(message, type = '') {
  const box = $('notice');

  box.textContent = message;
  box.className = `notice${type ? ` ${type}` : ''}`;
}

function formatDateTime(value) {
  if (!value) return '-';

  return String(value).replace('T', ' ').replace(/\.\d+$/, '');
}

function createStatusBadge(text, variant) {
  const badge = document.createElement('span');

  badge.className = `badge ${variant}`;
  badge.textContent = text;

  return badge;
}

function createButton(label, className, onClick) {
  const button = document.createElement('button');

  button.type = 'button';
  button.className = className;
  button.textContent = label;
  button.addEventListener('click', onClick);

  return button;
}

// แถวว่างของตาราง (ไม่มีข้อมูล / โหลดไม่สำเร็จ)
function renderEmptyRow(tbody, colSpan, message) {
  const row = document.createElement('tr');
  const cell = document.createElement('td');

  cell.colSpan = colSpan;
  cell.className = 'empty';
  cell.textContent = message;

  row.append(cell);
  tbody.replaceChildren(row);
}

// เติมค่าข้อความธรรมดาลงในแถว (ใช้ textContent ป้องกัน XSS)
function appendTextCells(row, values) {
  for (const value of values) {
    const cell = document.createElement('td');

    cell.textContent = String(value ?? '-');
    row.append(cell);
  }
}

/* ---------- Dialog (แทน prompt / confirm ของ browser) ---------- */

let dialogElement = null;

function ensureDialog() {
  if (dialogElement) return dialogElement;

  dialogElement = document.createElement('dialog');
  dialogElement.className = 'dialog';

  dialogElement.innerHTML = `
    <div class="dialog-head"></div>
    <form class="dialog-body" method="dialog">
      <h2 data-dialog-title></h2>
      <p class="dialog-message" data-dialog-message></p>

      <div data-dialog-reason-wrap>
        <label for="dialogReason" data-dialog-reason-label></label>
        <textarea
          class="dialog-textarea"
          id="dialogReason"
          maxlength="500"
        ></textarea>
      </div>

      <div class="dialog-actions">
        <button
          class="btn outline"
          type="button"
          data-dialog-cancel
        >
          ยกเลิก
        </button>
        <button class="btn" type="submit" data-dialog-confirm></button>
      </div>
    </form>
  `;

  document.body.append(dialogElement);

  return dialogElement;
}

/**
 * เปิด dialog ยืนยัน (พร้อมช่องเหตุผลถ้าต้องการ)
 * คืนค่า: { reason } ถ้ากดยืนยัน หรือ null ถ้ากดยกเลิก
 */
function openDialog({
  title,
  message = '',
  confirmLabel = 'ยืนยัน',
  reasonLabel = null,
  reasonPlaceholder = '',
  success = false,
}) {
  const dialog = ensureDialog();
  const form = dialog.querySelector('form');
  const reasonWrap = dialog.querySelector('[data-dialog-reason-wrap]');
  const reasonInput = dialog.querySelector('#dialogReason');
  const confirmButton = dialog.querySelector('[data-dialog-confirm]');
  const cancelButton = dialog.querySelector('[data-dialog-cancel]');

  dialog.querySelector('[data-dialog-title]').textContent = title;
  dialog.querySelector('[data-dialog-message]').textContent = message;
  dialog.querySelector('[data-dialog-message]').hidden = !message;

  reasonWrap.hidden = !reasonLabel;
  reasonInput.required = Boolean(reasonLabel);
  reasonInput.value = '';
  reasonInput.placeholder = reasonPlaceholder;
  dialog.querySelector('[data-dialog-reason-label]').textContent =
    reasonLabel || '';

  confirmButton.textContent = confirmLabel;
  confirmButton.className = success ? 'btn success' : 'btn';

  return new Promise((resolve) => {
    const cleanup = () => {
      form.removeEventListener('submit', onSubmit);
      cancelButton.removeEventListener('click', onCancel);
      dialog.removeEventListener('cancel', onCancel);
    };

    const onSubmit = (event) => {
      event.preventDefault();

      const reason = reasonInput.value.trim();

      if (reasonLabel && !reason) {
        reasonInput.focus();
        return;
      }

      cleanup();
      dialog.close();
      resolve({ reason });
    };

    const onCancel = (event) => {
      event.preventDefault();
      cleanup();
      dialog.close();
      resolve(null);
    };

    form.addEventListener('submit', onSubmit);
    cancelButton.addEventListener('click', onCancel);
    dialog.addEventListener('cancel', onCancel);

    dialog.showModal();

    if (reasonLabel) reasonInput.focus();
  });
}

/* ---------- Init ---------- */

ensureLoggedIn();
