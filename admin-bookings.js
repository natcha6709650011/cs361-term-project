
(function () {
  // Local (dev-server.js): /api/v1/<*> | Amplify rewrite: /api/<*> -> API Gateway /v1/<*>
  const API_BASE_URL = window.location.port === "5501" ? "/api/v1" : "/api";
  const BOOKINGS_URL = `${API_BASE_URL}/admin/bookings`;

  const $ = (id) => document.getElementById(id);
  const rowsEl = $("bookingRows");
  const statusEl = $("adminStatus");
  const refreshBtn = $("refreshBtn");
  const searchInput = $("fSearch");
  const statusFilter = $("fStatus");
  const attendanceFilter = $("fAttendance");
  const dateFilter = $("fDate");

  let bookings = [];

  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[c]));

  async function api(url) {
    const res = await fetch(url, {
      method: "GET",
      credentials: "include",
      headers: {
        "Content-Type": "application/json"
      }
    });

    let data = null;

    try {
      data = await res.json();
    } catch (error) {
      // Keep data null if response is not JSON.
    }

    if (res.status === 401) {
      window.location.href = "login.html";
      throw new Error("กรุณาเข้าสู่ระบบใหม่");
    }

    if (res.status === 403) {
      throw new Error(
        "บัญชีนี้ไม่มีสิทธิ์เข้าถึงหน้าติดตามการจอง (ต้องเป็น APPROVER หรือ FACILITY_ADMIN)"
      );
    }

    if (!res.ok) {
      throw new Error(
        (data && (data.message || data.error)) ||
        `เกิดข้อผิดพลาด (${res.status})`
      );
    }

    return data;
  }

  function showStatus(message, isError) {
    statusEl.textContent = message;
    statusEl.classList.toggle("is-error", Boolean(isError));
    statusEl.hidden = !message;
  }

  function getItems(data) {
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.bookings)) return data.bookings;
    if (Array.isArray(data?.items)) return data.items;
    return [];
  }

  function valueOf(item, ...keys) {
    for (const key of keys) {
      if (
        item[key] !== undefined &&
        item[key] !== null &&
        item[key] !== ""
      ) {
        return item[key];
      }
    }

    return null;
  }

  // Backend returns date as YYYY-MM-DD.
  function formatDate(value) {
    if (!value) return "—";

    const raw = String(value).trim();
    const match = raw.match(/^(\d{4})-(\d{2})-(\d{2})$/);

    if (match) {
      return `${match[3]}/${match[2]}/${match[1]}`;
    }

    return raw;
  }

  // Format MySQL DATETIME without converting timezone.
  function formatDateTime(value) {
    if (!value) return "—";

    const raw = String(value).trim().replace("T", " ");
    const match = raw.match(
      /^(\d{4})-(\d{2})-(\d{2})[ ](\d{2}):(\d{2})/
    );

    if (match) {
      return `${match[3]}/${match[2]}/${match[1]} ${match[4]}:${match[5]}`;
    }

    return raw;
  }

  function normalizeStatus(value) {
    return String(value ?? "").trim().toUpperCase();
  }

  // Booking status labels.
  const bookingStatus = (value) => {
    const status = normalizeStatus(value);

    const labels = {
      PENDING: ["รออนุมัติ", "is-warn"],
      APPROVED: ["อนุมัติแล้ว", "is-good"],
      REJECTED: ["ไม่อนุมัติ", "is-bad"],
      CANCELLED: ["ยกเลิก", ""],
      NO_SHOW: ["ไม่มาใช้งาน", "is-bad"]
    };

    return labels[status] || [value || "—", ""];
  };

  // Attendance status labels.
  const attendanceStatus = (value) => {
    const status = normalizeStatus(value);

    const labels = {
      NOT_CHECKED_IN: ["ยังไม่ Check-in", "is-warn"],
      CHECKED_IN: ["กำลังใช้งาน", "is-good"],
      COMPLETED: ["ใช้งานเสร็จแล้ว", "is-good"],
      NO_SHOW: ["ไม่มาใช้งาน", "is-bad"]
    };

    return labels[status] || [value || "—", ""];
  };

  function badge(pair) {
    return `
      <span class="status-badge ${pair[1]}">
        ${esc(pair[0])}
      </span>
    `;
  }

  // Update summary cards.
  function updateSummary(list) {
    $("totalCount").textContent = list.length;

    $("pendingCount").textContent = list.filter(
      (booking) =>
        normalizeStatus(booking.status) === "PENDING"
    ).length;

    $("approvedCount").textContent = list.filter(
      (booking) =>
        normalizeStatus(booking.status) === "APPROVED"
    ).length;

    $("noShowCount").textContent = list.filter(
      (booking) =>
        normalizeStatus(booking.status) === "NO_SHOW" ||
        normalizeStatus(
          valueOf(booking, "attendanceStatus", "attendance_status")
        ) === "NO_SHOW"
    ).length;
  }

  // Search and filter bookings.
  function render() {
    const query = searchInput.value.trim().toLowerCase();

    const selectedStatus =
      normalizeStatus(statusFilter.value);

    const selectedAttendance =
      normalizeStatus(attendanceFilter.value);

    // input[type=date] returns YYYY-MM-DD.
    const selectedDate = dateFilter.value;

    const filtered = bookings.filter((booking) => {

      // Search username, room number and purpose.
      const username = String(
        valueOf(
          booking,
          "bookerUsername",
          "booker_username",
          "username"
        ) ?? ""
      ).toLowerCase();

      const roomNumber = String(
        valueOf(
          booking,
          "roomNumber",
          "room_number"
        ) ?? ""
      ).toLowerCase();

      const purpose = String(
        valueOf(
          booking,
          "purpose",
          "title"
        ) ?? ""
      ).toLowerCase();

      const matchesSearch =
        !query ||
        username.includes(query) ||
        roomNumber.includes(query) ||
        purpose.includes(query);

      // Filter booking status.
      const matchesBookingStatus =
        !selectedStatus ||
        normalizeStatus(booking.status) === selectedStatus;

      // Filter check-in / attendance status.
      const matchesAttendanceStatus =
        !selectedAttendance ||
        normalizeStatus(
          valueOf(
            booking,
            "attendanceStatus",
            "attendance_status"
          )
        ) === selectedAttendance;

      // IMPORTANT:
      // Booking Lambda sends the date in `date`.
      // It does NOT send a full datetime in `start_time`.
      const bookingDate = String(
        valueOf(
          booking,
          "date",
          "booking_date",
          "bookingDate"
        ) ?? ""
      ).slice(0, 10);

      const matchesDate =
        !selectedDate ||
        bookingDate === selectedDate;

      return (
        matchesSearch &&
        matchesBookingStatus &&
        matchesAttendanceStatus &&
        matchesDate
      );
    });

    // Render filtered results.
    rowsEl.innerHTML = filtered.length
      ? filtered.map((booking) => {

          const statusPair =
            bookingStatus(booking.status);

          const attendancePair =
            attendanceStatus(
              valueOf(
                booking,
                "attendanceStatus",
                "attendance_status"
              )
            );

          return `
            <tr>
              <td>
                ${esc(
                  valueOf(
                    booking,
                    "bookerUsername",
                    "booker_username",
                    "username"
                  ) || "—"
                )}
              </td>

              <td>
                ${esc(
                  valueOf(
                    booking,
                    "roomNumber",
                    "room_number"
                  ) || "—"
                )}
                <br>
                <small>
                  ${esc(
                    valueOf(
                      booking,
                      "roomType",
                      "room_type"
                    ) || "—"
                  )}
                </small>
              </td>

              <td class="monitor-time">
                ${esc(
                  formatDate(
                    valueOf(
                      booking,
                      "date",
                      "booking_date",
                      "bookingDate"
                    )
                  )
                )}
                <br>
                ${esc(
                  valueOf(
                    booking,
                    "startTime",
                    "start_time"
                  ) || "—"
                )}
                ถึง
                ${esc(
                  valueOf(
                    booking,
                    "endTime",
                    "end_time"
                  ) || "—"
                )}
              </td>

              <td class="monitor-purpose">
                ${esc(
                  valueOf(
                    booking,
                    "purpose",
                    "title",
                    "request_note"
                  ) || "—"
                )}
              </td>

              <td>
                ${badge(statusPair)}
              </td>

              <td>
                ${badge(attendancePair)}
              </td>

              <td class="monitor-time">
                ${esc(
                  formatDateTime(
                    valueOf(
                      booking,
                      "checkedInAt",
                      "checked_in_at"
                    )
                  )
                )}
              </td>

              <td class="monitor-time">
                ${esc(
                  formatDateTime(
                    valueOf(
                      booking,
                      "actualUsageStart",
                      "actual_usage_start"
                    )
                  )
                )}
              </td>

              <td class="monitor-time">
                ${esc(
                  formatDateTime(
                    valueOf(
                      booking,
                      "actualUsageEnd",
                      "actual_usage_end"
                    )
                  )
                )}
              </td>

              <td class="monitor-time">
                ${esc(
                  formatDateTime(
                    valueOf(
                      booking,
                      "noShowAt",
                      "no_show_at"
                    )
                  )
                )}
              </td>
            </tr>
          `;
        }).join("")
      : `
        <tr>
          <td colspan="10" class="admin-empty">
            ไม่พบรายการจองที่ตรงกับเงื่อนไข
          </td>
        </tr>
      `;
  }

  // Load all bookings from API.
  async function loadBookings() {
    refreshBtn.disabled = true;

    showStatus("กำลังโหลดข้อมูล...", false);

    rowsEl.innerHTML = `
      <tr>
        <td colspan="10" class="admin-empty">
          กำลังโหลดข้อมูล...
        </td>
      </tr>
    `;

    try {
      const data = await api(BOOKINGS_URL);

      bookings = getItems(data);

      updateSummary(bookings);
      render();

      showStatus(
        `โหลดข้อมูลสำเร็จ ${bookings.length} รายการ`,
        false
      );

    } catch (error) {
      bookings = [];

      updateSummary(bookings);

      rowsEl.innerHTML = `
        <tr>
          <td colspan="10" class="admin-empty">
            ${esc(error.message)}
          </td>
        </tr>
      `;

      showStatus(error.message, true);

    } finally {
      refreshBtn.disabled = false;
    }
  }

  // Search updates while typing.
  searchInput.addEventListener("input", render);

  // Dropdown filters update when selection changes.
  statusFilter.addEventListener("change", render);
  attendanceFilter.addEventListener("change", render);

  // Date filter updates when a date is selected.
  dateFilter.addEventListener("change", render);

  // Refresh button.
  refreshBtn.addEventListener("click", loadBookings);

  // Backend enforces APPROVER / FACILITY_ADMIN access.
  loadBookings();

})();
