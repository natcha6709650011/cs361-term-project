/* =========================================================
   V3 Approval - หน้าอนุมัติ / ปฏิเสธคำขอจอง (APPROVER)
   ต้องโหลด admin-common.js ก่อนไฟล์นี้
   ========================================================= */

const STATUS_VARIANTS = {
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected',
};

/* ---------- Render ---------- */

function renderRows(items) {
  const tbody = $('rows');

  $('count').textContent = `${items.length} รายการที่รออนุมัติ`;

  if (!items.length) {
    renderEmptyRow(tbody, 6, 'ไม่มีคำขอที่รออนุมัติ');
    return;
  }

  tbody.replaceChildren();

  for (const item of items) {
    const row = document.createElement('tr');

    appendTextCells(row, [
      item.booking_id,
      item.room_number ?? item.room_id,
      item.title,
      `${formatDateTime(item.start_time)} – ${formatDateTime(item.end_time)}`,
    ]);

    // สถานะ
    const statusCell = document.createElement('td');

    statusCell.append(
      createStatusBadge(
        item.status,
        STATUS_VARIANTS[item.status] || 'pending'
      )
    );
    row.append(statusCell);

    // ปุ่มอนุมัติ / ปฏิเสธ
    const actionCell = document.createElement('td');
    const group = document.createElement('div');

    group.className = 'row-actions';
    group.append(
      createButton('อนุมัติ', 'btn success small', () =>
        approveBooking(item)
      ),
      createButton('ปฏิเสธ', 'btn small', () => rejectBooking(item))
    );

    actionCell.append(group);
    row.append(actionCell);
    tbody.append(row);
  }
}

/* ---------- Actions ---------- */

async function loadPending() {
  $('reload').disabled = true;
  setNotice('กำลังโหลดคำขอ...');

  try {
    const data = await api('/approvals/pending');

    renderRows(data.items || []);
    setNotice('โหลดข้อมูลสำเร็จ', 'success');
  } catch (error) {
    renderRows([]);
    $('count').textContent = '';
    setNotice(error.message, 'error');
  } finally {
    $('reload').disabled = false;
  }
}

function setButtonsDisabled(disabled) {
  document
    .querySelectorAll('#rows button, #reload')
    .forEach((button) => {
      button.disabled = disabled;
    });
}

async function submitDecision(bookingId, action, reason = null) {
  const label = action === 'APPROVED' ? 'อนุมัติ' : 'ปฏิเสธ';

  setButtonsDisabled(true);
  setNotice(`กำลัง${label}คำขอ #${bookingId}...`);

  try {
    await api(`/approvals/${bookingId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ action, reason }),
    });

    await loadPending();
    setNotice(`${label}คำขอ #${bookingId} สำเร็จ`, 'success');
  } catch (error) {
    setNotice(error.message, 'error');
    setButtonsDisabled(false);
  }
}

async function approveBooking(item) {
  const result = await openDialog({
    title: `อนุมัติคำขอ #${item.booking_id}`,
    message: `ห้อง ${item.room_number ?? item.room_id} – ${item.title}`,
    confirmLabel: 'ยืนยันการอนุมัติ',
    success: true,
  });

  if (result) {
    await submitDecision(item.booking_id, 'APPROVED');
  }
}

async function rejectBooking(item) {
  const result = await openDialog({
    title: `ปฏิเสธคำขอ #${item.booking_id}`,
    message: `ห้อง ${item.room_number ?? item.room_id} – ${item.title}`,
    confirmLabel: 'ยืนยันการปฏิเสธ',
    reasonLabel: 'เหตุผล (จำเป็น)',
    reasonPlaceholder: 'เช่น ห้องถูกจัดไว้สำหรับการเรียนการสอน',
  });

  if (result) {
    await submitDecision(item.booking_id, 'REJECTED', result.reason);
  }
}

/* ---------- Init ---------- */

$('reload').addEventListener('click', loadPending);

initAdminPage('is_approver').then((allowed) => {
  if (allowed) loadPending();
});
