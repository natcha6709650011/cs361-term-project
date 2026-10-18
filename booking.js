(function myBookingsPage() {
  const statusLabels = {
    PENDING: "รออนุมัติ",
    APPROVED: "อนุมัติแล้ว",
    REJECTED: "ปฏิเสธ",
    CANCELLED: "ยกเลิก",
  };
  let activeStatus = "ALL";
  let activeBookingId = null;
  let lastFocusedElement = null;
  let bookingData = [];
  let isLoading = false;

  const dateFormatter = new Intl.DateTimeFormat("th-TH", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });

  function formatDate(value) {
    return dateFormatter.format(new Date(`${value}T00:00:00`));
  }

  function updateCounts() {
    document.querySelectorAll("[data-count]").forEach((element) => {
      const status = element.dataset.count;
      const count = status === "ALL" ? bookingData.length : bookingData.filter((item) => item.status === status).length;
      element.textContent = `(${count})`;
    });
  }

  function setListState(state) {
    const loading = document.querySelector("#my-bookings-loading");
    const error = document.querySelector("#my-bookings-error");
    const empty = document.querySelector("#my-bookings-empty");
    const table = document.querySelector("[data-booking-table-wrap]");

    loading.hidden = state !== "loading";
    error.hidden = state !== "error";

    if (state === "loading" || state === "error") {
      empty.hidden = true;
      table.hidden = true;
    }
  }

  async function loadBookings() {
    isLoading = true;
    setListState("loading");

    try {
      if (!window.BookingService) throw new Error("Booking service is unavailable");
      bookingData = await window.BookingService.getMyBookings();
      isLoading = false;
      updateCounts();
      renderBookings();
    } catch (error) {
      console.error("Unable to load bookings:", error);
      bookingData = [];
      isLoading = false;
      updateCounts();
      setListState("error");
    }
  }

  function getFilteredBookings() {
    const search = document.querySelector("#booking-search")?.value.trim().toLowerCase() || "";
    const date = document.querySelector("#booking-date-filter")?.value || "";

    return bookingData.filter((booking) => {
      const matchesStatus = activeStatus === "ALL" || booking.status === activeStatus;
      const matchesDate = !date || booking.date === date;
      const searchable = `${booking.room} ${booking.purpose}`.toLowerCase();
      const matchesSearch = !search || searchable.includes(search);
      return matchesStatus && matchesDate && matchesSearch;
    });
  }

  function renderBookings() {
    if (isLoading) return;
    const body = document.querySelector("#my-bookings-body");
    const empty = document.querySelector("#my-bookings-empty");
    const table = document.querySelector("[data-booking-table-wrap]");
    const bookings = getFilteredBookings();

    setListState("ready");
    body.replaceChildren();
    empty.hidden = bookings.length !== 0;
    table.hidden = bookings.length === 0;

    bookings.forEach((booking) => {
      const row = document.createElement("tr");
      const canManage = booking.status === "PENDING";
      row.innerHTML = `
        <td>${formatDate(booking.date)}</td>
        <td>${booking.startTime} - ${booking.endTime}</td>
        <td><strong>${booking.room}</strong></td>
        <td>${booking.roomType}</td>
        <td>${booking.purpose}</td>
        <td>${booking.participants}</td>
        <td><span class="booking-status booking-status--${booking.status.toLowerCase()}">${statusLabels[booking.status]}</span></td>
        <td class="booking-row-actions">
          <button class="booking-detail-button" type="button" data-booking-detail="${booking.id}">ดูรายละเอียด</button>
          ${canManage ? `<div class="booking-action-menu"><button class="booking-more-button" type="button" data-booking-menu="${booking.id}" aria-label="จัดการรายการ ${booking.room}" aria-expanded="false">⋯</button><div class="booking-action-popover" hidden><button type="button" data-booking-edit="${booking.id}">แก้ไข</button><button type="button" data-booking-cancel="${booking.id}">ยกเลิก</button></div></div>` : ""}
        </td>
      `;
      body.appendChild(row);
    });
  }

  function findBooking(id) {
    return bookingData.find((booking) => booking.id === id);
  }

  function getDialog(id) {
    return document.querySelector(id);
  }

  function openDialog(id, trigger) {
    lastFocusedElement = trigger || document.activeElement;
    const dialog = getDialog(id);
    dialog.hidden = false;
    document.body.style.overflow = "hidden";
    dialog.querySelector("button, input, select, textarea")?.focus();
  }

  function closeDialogs() {
    document.querySelectorAll(".booking-dialog").forEach((dialog) => {
      dialog.hidden = true;
    });
    document.body.style.overflow = "";
    lastFocusedElement?.focus();
  }

  function setText(selector, value) {
    const element = document.querySelector(selector);
    if (element) element.textContent = value;
  }

  function openDetail(booking, trigger) {
    activeBookingId = booking.id;
    setText("[data-detail-room]", booking.room);
    setText("[data-detail-room-subtitle]", booking.roomType);
    setText("[data-detail-date]", formatDate(booking.date));
    setText("[data-detail-time]", `${booking.startTime} - ${booking.endTime}`);
    setText("[data-detail-type]", booking.roomType);
    setText("[data-detail-purpose]", booking.purpose);
    setText("[data-detail-participants]", `${booking.participants} คน`);

    const status = document.querySelector("[data-detail-status]");
    status.textContent = statusLabels[booking.status];
    status.className = `booking-status booking-status--${booking.status.toLowerCase()}`;

    const reasonRow = document.querySelector("[data-detail-reason-row]");
    reasonRow.hidden = !booking.rejectionReason;
    setText("[data-detail-reason]", booking.rejectionReason || "");

    document.querySelector("[data-detail-edit]").hidden = booking.status !== "PENDING";
    document.querySelector("[data-detail-cancel]").hidden = booking.status !== "PENDING";
    openDialog("#booking-detail-dialog", trigger);
  }

  function syncDatePicker(selector, value) {
    const source = document.querySelector(selector);
    const picker = source.closest("[data-date-picker]");
    const date = new Date(`${value}T00:00:00`);
    source.value = value;
    picker.querySelector(".date-trigger span").textContent = `${String(date.getDate()).padStart(2, "0")}/${String(date.getMonth() + 1).padStart(2, "0")}/${date.getFullYear()}`;
    picker.querySelector(".date-trigger").classList.remove("is-placeholder");
  }

  function syncTimePicker(selector, value) {
    const source = document.querySelector(selector);
    const picker = source.closest("[data-time-picker]");
    source.value = value;
    source.dispatchEvent(new Event("change", { bubbles: true }));
    picker.querySelectorAll(".time-option").forEach((option) => {
      option.setAttribute("aria-selected", String(option.dataset.value === value));
    });
  }

  function openEdit(booking, trigger) {
    activeBookingId = booking.id;
    setText("[data-edit-room]", booking.room);
    syncDatePicker("#edit-booking-date", booking.date);
    document.querySelector("#edit-booking-purpose").value = booking.purpose;
    document.querySelector("#edit-booking-participants").value = booking.participants;
    syncTimePicker("#edit-booking-start", booking.startTime);
    syncTimePicker("#edit-booking-end", booking.endTime);
    const message = document.querySelector("#booking-edit-message");
    message.hidden = true;
    message.textContent = "";
    openDialog("#booking-edit-dialog", trigger);
  }

  function openCancel(booking, trigger) {
    activeBookingId = booking.id;
    setText("[data-cancel-room]", booking.room);
    setText("[data-cancel-date]", `วันที่ ${formatDate(booking.date)}`);
    setText("[data-cancel-time]", `เวลา ${booking.startTime} - ${booking.endTime}`);
    const error = document.querySelector("[data-cancel-error]");
    if (error) {
      error.hidden = true;
      error.textContent = "";
    }
    openDialog("#booking-cancel-dialog", trigger);
  }

  function openConflict(date, startTime, endTime) {
    setText("[data-conflict-date]", `วันที่ ${formatDate(date)}`);
    setText("[data-conflict-time]", `เวลา ${startTime} - ${endTime}`);
    getDialog("#booking-edit-dialog").hidden = true;
    openDialog("#booking-conflict-dialog", document.querySelector("#booking-edit-form button[type='submit']"));
  }

  function setupActions() {
    document.querySelector("#my-bookings-body").addEventListener("click", (event) => {
      const detail = event.target.closest("[data-booking-detail]");
      const menu = event.target.closest("[data-booking-menu]");
      const edit = event.target.closest("[data-booking-edit]");
      const cancel = event.target.closest("[data-booking-cancel]");
      const booking = findBooking(detail?.dataset.bookingDetail || menu?.dataset.bookingMenu || edit?.dataset.bookingEdit || cancel?.dataset.bookingCancel);

      if (detail && booking) openDetail(booking, detail);
      if (menu) {
        const actionMenu = menu.closest(".booking-action-menu");
        const popover = actionMenu.querySelector(".booking-action-popover");
        const isOpen = !popover.hidden;
        document.querySelectorAll(".booking-action-popover").forEach((item) => { item.hidden = true; });
        popover.hidden = isOpen;
        menu.setAttribute("aria-expanded", String(!isOpen));
      }
      if (edit && booking) openEdit(booking, edit);
      if (cancel && booking) openCancel(booking, cancel);
    });

    document.addEventListener("click", (event) => {
      if (!event.target.closest(".booking-action-menu")) {
        document.querySelectorAll(".booking-action-popover").forEach((item) => { item.hidden = true; });
        document.querySelectorAll("[data-booking-menu]").forEach((item) => item.setAttribute("aria-expanded", "false"));
      }
    });

    document.querySelectorAll("[data-dialog-close]").forEach((button) => button.addEventListener("click", closeDialogs));
    document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeDialogs(); });
    document.querySelector("[data-detail-edit]").addEventListener("click", (event) => openEdit(findBooking(activeBookingId), event.currentTarget));
    document.querySelector("[data-detail-cancel]").addEventListener("click", (event) => openCancel(findBooking(activeBookingId), event.currentTarget));
    document.querySelector("[data-conflict-edit]").addEventListener("click", () => {
      getDialog("#booking-conflict-dialog").hidden = true;
      getDialog("#booking-edit-dialog").hidden = false;
      document.querySelector("#edit-booking-start").closest("[data-time-picker]").querySelector(".time-trigger").focus();
    });

    document.querySelector("#booking-edit-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const booking = findBooking(activeBookingId);
      const startTime = document.querySelector("#edit-booking-start").value;
      const endTime = document.querySelector("#edit-booking-end").value;
      const message = document.querySelector("#booking-edit-message");

      if (startTime >= endTime) {
        message.textContent = "เวลาเริ่มต้องอยู่ก่อนเวลาสิ้นสุด";
        message.hidden = false;
        return;
      }

      const purpose = document.querySelector("#edit-booking-purpose").value.trim();
      const participants = Number(document.querySelector("#edit-booking-participants").value);

      if (!purpose || !Number.isInteger(participants) || participants < 1) {
        message.textContent = "กรุณาระบุวัตถุประสงค์และจำนวนผู้เข้าร่วมให้ถูกต้อง";
        message.hidden = false;
        return;
      }

      const date = document.querySelector("#edit-booking-date").value;
      const submitButton = event.currentTarget.querySelector('button[type="submit"]');
      submitButton.disabled = true;
      submitButton.textContent = "กำลังบันทึก...";
      message.hidden = true;

      try {
        if (!window.BookingService) throw new Error("Booking service is unavailable");
        const result = await window.BookingService.updateBooking(booking.id, {
          date,
          startTime,
          endTime,
          purpose,
          participants,
        });
        const index = bookingData.findIndex((item) => item.id === result.booking.id);
        if (index !== -1) bookingData[index] = result.booking;
        closeDialogs();
        renderBookings();
      } catch (error) {
        console.error("Unable to update booking:", error);
        if (error.code === "BOOKING_CONFLICT") {
          openConflict(date, startTime, endTime);
        } else {
          message.textContent = "ไม่สามารถบันทึกการแก้ไขได้ กรุณาลองใหม่อีกครั้ง";
          message.hidden = false;
        }
      } finally {
        submitButton.disabled = false;
        submitButton.textContent = "บันทึกการแก้ไข";
      }
    });

    document.querySelector("[data-confirm-cancel]").addEventListener("click", async (event) => {
      const booking = findBooking(activeBookingId);
      const button = event.currentTarget;
      const errorMessage = document.querySelector("[data-cancel-error]");
      button.disabled = true;
      button.textContent = "กำลังยกเลิก...";
      if (errorMessage) errorMessage.hidden = true;

      try {
        if (!window.BookingService) throw new Error("Booking service is unavailable");
        const result = await window.BookingService.cancelBooking(booking.id);
        const index = bookingData.findIndex((item) => item.id === result.booking.id);
        if (index !== -1) bookingData[index] = result.booking;
        closeDialogs();
        updateCounts();
        renderBookings();
      } catch (error) {
        console.error("Unable to cancel booking:", error);
        if (errorMessage) {
          errorMessage.textContent = "ไม่สามารถยกเลิกคำขอได้ กรุณาลองใหม่อีกครั้ง";
          errorMessage.hidden = false;
        }
      } finally {
        button.disabled = false;
        button.textContent = "ยืนยันการยกเลิก";
      }
    });

    document.querySelector("[data-bookings-retry]").addEventListener("click", loadBookings);
  }

  function setupFilters() {
    document.querySelectorAll("[data-status-filter]").forEach((button) => {
      button.addEventListener("click", () => {
        activeStatus = button.dataset.statusFilter;
        document.querySelectorAll("[data-status-filter]").forEach((tab) => {
          tab.setAttribute("aria-selected", String(tab === button));
        });
        renderBookings();
      });
    });

    document.querySelector("#booking-search")?.addEventListener("input", renderBookings);
    document.querySelector("#booking-date-filter")?.addEventListener("change", renderBookings);
  }

  setupFilters();
  setupActions();
  loadBookings();
})();
