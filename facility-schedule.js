/* =========================================================
   V3 Fixed Facility Schedule (FACILITY_ADMIN)
   - สร้างตารางประจำรายสัปดาห์
   - ปล่อย / คืนตารางเป็นรายวัน
   ต้องโหลด admin-common.js ก่อนไฟล์นี้
   ========================================================= */

const WEEKDAYS = [
  'วันจันทร์',
  'วันอังคาร',
  'วันพุธ',
  'วันพฤหัสบดี',
  'วันศุกร์',
  'วันเสาร์',
  'วันอาทิตย์',
];

function selectedDate() {
  return $('filterDate').value;
}

function toDateInputValue(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  return `${year}-${month}-${day}`;
}

function timeText(value) {
  return String(value).slice(0, 5);
}

/* ---------- Render ---------- */

function createStateCell(rule) {
  const cell = document.createElement('td');

  if (!selectedDate()) {
    cell.textContent = 'เลือกวันที่เพื่อตรวจ';
    return cell;
  }

  cell.append(
    rule.is_blocked_on_date
      ? createStatusBadge('ล็อกตามตาราง', 'locked')
      : createStatusBadge('ปล่อยให้จอง', 'released')
  );

  return cell;
}

function createActionCell(rule) {
  const cell = document.createElement('td');
  const group = document.createElement('div');
  const hasDate = Boolean(selectedDate());

  group.className = 'row-actions';

  const release = createButton('ปล่อยวันนี้', 'btn outline small', () =>
    changeException(rule, 'RELEASE')
  );
  release.disabled = !hasDate || !rule.is_blocked_on_date;

  const restore = createButton('คืนตารางวันนี้', 'btn outline small', () =>
    changeException(rule, 'RESTORE')
  );
  restore.disabled = !hasDate || rule.is_blocked_on_date;

  group.append(release, restore);
  cell.append(group);

  return cell;
}

function renderRows(items) {
  const tbody = $('rows');

  if (!items.length) {
    renderEmptyRow(
      tbody,
      7,
      selectedDate()
        ? 'ไม่พบตารางประจำที่ตรงกับวันที่เลือก'
        : 'ไม่พบตารางประจำ'
    );
    return;
  }

  tbody.replaceChildren();

  for (const rule of items) {
    const row = document.createElement('tr');

    appendTextCells(row, [
      rule.schedule_id,
      rule.room_number ?? rule.room_id,
      rule.title,
      `${WEEKDAYS[Number(rule.weekday)]} ` +
        `${timeText(rule.start_time)}–${timeText(rule.end_time)}`,
      `${rule.valid_from} ถึง ${rule.valid_until}`,
    ]);

    row.append(createStateCell(rule), createActionCell(rule));
    tbody.append(row);
  }
}

/* ---------- Actions ---------- */

async function loadSchedules() {
  setNotice('กำลังโหลดตารางประจำ...');
  $('reload').disabled = true;

  try {
    const params = new URLSearchParams();

    if (selectedDate()) params.set('date', selectedDate());
    if ($('filterRoom').value) params.set('room_id', $('filterRoom').value);

    const query = params.toString() ? `?${params}` : '';
    const data = await api(`/facility-schedule-rules${query}`);
    const items = data.items || [];

    renderRows(items);
    setNotice(`โหลดตารางประจำ ${items.length} รายการ`, 'success');
  } catch (error) {
    renderRows([]);
    setNotice(error.message, 'error');
  } finally {
    $('reload').disabled = false;
  }
}

async function changeException(rule, action) {
  const date = selectedDate();

  if (!date) {
    setNotice('กรุณาเลือกวันที่ก่อน', 'error');
    return;
  }

  const isRelease = action === 'RELEASE';
  const roomLabel = rule.room_number ?? rule.room_id;

  const result = await openDialog({
    title: isRelease ? 'ปล่อยตารางประจำวันนี้' : 'คืนตารางประจำวันนี้',
    message:
      `${isRelease ? 'เปิดช่วงเวลานี้ให้จอง' : 'กลับมาล็อกตามตารางประจำ'} ` +
      `สำหรับวันที่ ${date} ห้อง ${roomLabel}`,
    confirmLabel: isRelease ? 'ยืนยันการปล่อยตาราง' : 'ยืนยันการคืนตาราง',
    reasonLabel: isRelease
      ? 'เหตุผลที่ปล่อยตารางประจำวันนี้ (จำเป็น)'
      : 'เหตุผลที่ต้องการคืนตารางประจำวันนี้ (จำเป็น)',
    reasonPlaceholder: isRelease ? 'เช่น อาจารย์ไม่ได้สอนในสัปดาห์นี้' : '',
  });

  if (!result) return;

  try {
    const out = await api(
      `/facility-schedule-rules/${rule.schedule_id}/exceptions`,
      {
        method: 'POST',
        body: JSON.stringify({ date, action, reason: result.reason }),
      }
    );

    await loadSchedules();
    setNotice(out.message || 'บันทึกข้อยกเว้นสำเร็จ', 'success');
  } catch (error) {
    setNotice(error.message, 'error');
  }
}

async function createSchedule(event) {
  event.preventDefault();

  const payload = {
    room_id: Number($('roomId').value),
    title: $('title').value.trim(),
    weekday: Number($('weekday').value),
    start_time: $('startTime').value,
    end_time: $('endTime').value,
    valid_from: $('validFrom').value,
    valid_until: $('validUntil').value,
  };

  $('save').disabled = true;

  try {
    const out = await api('/facility-schedule-rules', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    event.target.reset();
    setDefaultDates();
    await loadSchedules();
    setNotice(`สร้างตารางประจำ #${out.schedule_id} สำเร็จ`, 'success');
  } catch (error) {
    setNotice(error.message, 'error');
  } finally {
    $('save').disabled = false;
  }
}

/* ---------- Init ---------- */

// ตั้งค่าเริ่มต้นเป็นวันนี้ ผู้ใช้เปลี่ยนเองได้
function setDefaultDates() {
  const today = new Date();

  $('validFrom').value = toDateInputValue(today);
  $('validUntil').value = `${today.getFullYear()}-12-31`;
}

$('scheduleForm').addEventListener('submit', createSchedule);
$('scheduleForm').addEventListener('reset', () => {
  // ให้ reset ทำงานก่อน แล้วค่อยใส่ค่าเริ่มต้นกลับ
  setTimeout(setDefaultDates, 0);
});
$('reload').addEventListener('click', loadSchedules);
$('filter').addEventListener('click', loadSchedules);

$('filterDate').value = toDateInputValue(new Date());
setDefaultDates();

initAdminPage('is_facility_admin').then((allowed) => {
  if (allowed) loadSchedules();
});
