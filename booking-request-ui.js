/*
 * V3 User Booking UI
 *
 * This file owns only the booking-request modal and delegates data operations
 * to booking-service.js. The service remains in mock mode until the team's
 * authenticated Booking API is available.
 */
(function bookingRequestUi() {
  let modal;
  let successModal;
  let form;
  let lastFocusedElement;
  let bookingContext;

  function getElement(selector) {
    return document.querySelector(selector);
  }

  function formatDate(dateValue) {
    const date = new Date(`${dateValue}T00:00:00`);

    return new Intl.DateTimeFormat("th-TH", {
      day: "numeric",
      month: "short",
      year: "numeric",
    }).format(date);
  }

  function getDuration(startTime, endTime) {
    const [startHours, startMinutes] = startTime.split(":").map(Number);
    const [endHours, endMinutes] = endTime.split(":").map(Number);
    const totalMinutes = endHours * 60 + endMinutes - (startHours * 60 + startMinutes);
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;

    if (minutes === 0) return `${hours} ชั่วโมง`;
    if (hours === 0) return `${minutes} นาที`;
    return `${hours} ชั่วโมง ${minutes} นาที`;
  }

  function setText(selector, value) {
    const element = getElement(selector);

    if (element) element.textContent = value || "ไม่ระบุ";
  }

  function resetFormMessage() {
    const error = getElement("[data-booking-form-error]");

    if (error) {
      error.hidden = true;
      error.textContent = "";
    }
  }

  function showFormMessage(message) {
    const error = getElement("[data-booking-form-error]");

    if (error) {
      error.hidden = false;
      error.textContent = message;
    }
  }

  function updateSummary() {
    const purpose = getElement("#booking-purpose")?.value.trim();
    const participants = getElement("#booking-participants")?.value;

    setText("[data-summary-purpose]", purpose || "-");
    setText(
      "[data-summary-participants]",
      participants ? `${participants} คน` : "-",
    );
  }

  function populateModal(context) {
    bookingContext = context;
    const { room, date, startTime, endTime } = context;
    const displayDate = formatDate(date);
    const roomImage = getElement("[data-booking-room-image]");
    const purpose = getElement("#booking-purpose");
    const participants = getElement("#booking-participants");

    document.querySelectorAll("[data-booking-room-name]").forEach((element) => {
      element.textContent = room.displayName;
    });
    getElement("[data-booking-date]").value = displayDate;
    getElement("[data-booking-start]").value = startTime;
    getElement("[data-booking-end]").value = endTime;
    setText("[data-booking-room-location]", `${room.type} ${room.floor ? `ชั้น ${room.floor}` : ""}`.trim());
    setText("[data-summary-date]", displayDate);
    setText("[data-summary-time]", `${startTime} - ${endTime} (${getDuration(startTime, endTime)})`);
    setText("[data-summary-type]", room.type);
    setText("[data-summary-building]", room.building);
    setText("[data-summary-floor]", room.floor ? `ชั้น ${room.floor}` : "ไม่ระบุ");
    setText("[data-summary-size]", room.size);

    if (roomImage) {
      roomImage.src = room.imageUrl || "assets/bor2-308.jpg";
      roomImage.alt = `รูปห้อง ${room.displayName}`;
    }

    if (purpose) purpose.value = "";
    if (participants) {
      participants.value = "";
      participants.max = room.capacity || "";
    }

    setText("[data-purpose-count]", "0");
    updateSummary();
    resetFormMessage();
  }

  function open(context) {
    if (!modal || !context) return;

    lastFocusedElement = document.activeElement;
    populateModal(context);
    modal.hidden = false;
    document.body.style.overflow = "hidden";
    getElement("#booking-purpose")?.focus();
  }

  function close() {
    if (!modal || modal.hidden) return;

    modal.hidden = true;
    document.body.style.overflow = "";
    lastFocusedElement?.focus();
  }

  function openSuccess(payload) {
    if (!successModal) return;

    setText("[data-success-room]", bookingContext.room.displayName);
    setText("[data-success-date]", formatDate(bookingContext.date));
    setText("[data-success-time]", `${bookingContext.startTime} - ${bookingContext.endTime}`);
    setText("[data-success-participants]", `${payload.participants} คน`);
    modal.hidden = true;
    successModal.hidden = false;
    successModal.querySelector("[data-booking-success-close]")?.focus();
  }

  function closeSuccess() {
    if (!successModal || successModal.hidden) return;

    successModal.hidden = true;
    document.body.style.overflow = "";
    lastFocusedElement?.focus();
  }

  async function handleSubmit(event) {
    event.preventDefault();
    resetFormMessage();

    const purpose = getElement("#booking-purpose")?.value.trim() || "";
    const participantInput = getElement("#booking-participants");
    const participants = Number(participantInput?.value);

    if (!purpose) {
      showFormMessage("กรุณาระบุวัตถุประสงค์การใช้ห้อง");
      getElement("#booking-purpose")?.focus();
      return;
    }

    if (!Number.isInteger(participants) || participants < 1) {
      showFormMessage("กรุณาระบุจำนวนผู้เข้าร่วมอย่างน้อย 1 คน");
      participantInput?.focus();
      return;
    }

    if (bookingContext.room.capacity && participants > bookingContext.room.capacity) {
      showFormMessage(`จำนวนผู้เข้าร่วมต้องไม่เกินความจุห้อง ${bookingContext.room.capacity} คน`);
      participantInput?.focus();
      return;
    }

    const submitButton = form.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.textContent = "กำลังส่งคำขอ...";

    try {
      if (!window.BookingService) throw new Error("Booking service is unavailable");

      const result = await window.BookingService.createBooking({
        roomNumber: bookingContext.room.number,
        date: bookingContext.date,
        startTime: bookingContext.startTime,
        endTime: bookingContext.endTime,
        purpose,
        participants,
      });

      if (result.success) {
        document.dispatchEvent(new CustomEvent("room-booking:created", {
          detail: {
            roomNumber: bookingContext.room.number,
            date: bookingContext.date,
          },
        }));
        openSuccess({ purpose, participants });
      } else if (result.isMock) {
        showFormMessage("นี่คือการส่งข้อมูลตัวอย่าง: เมื่อเชื่อม API แล้วคำขอจริงจะถูกบันทึกเป็นสถานะ “รออนุมัติ”");
      }
    } catch (error) {
      console.error("Unable to submit booking request:", error);
       if (error.code === "AUTH_REQUIRED") {
    const goLogin = confirm(
      "กรุณาเข้าสู่ระบบก่อนจองห้อง\n\nต้องการไปหน้าเข้าสู่ระบบหรือไม่?"
    );

    if (goLogin) {
      window.location.href = "login.html";
    }

    return;
  }

      showFormMessage(error.code === "BOOKING_CONFLICT"
        ? "ช่วงเวลานี้ไม่ว่างแล้ว กรุณาเลือกช่วงเวลาอื่น"
        : error.message || "ไม่สามารถส่งคำขอจองได้ กรุณาลองใหม่อีกครั้ง");
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "ส่งคำขอจอง";
    }
  }

  function setup() {
    modal = getElement("#booking-request-modal");
    successModal = getElement("#booking-success-modal");
    form = getElement("#booking-request-form");

    if (!modal || !form) return;

    modal.querySelectorAll("[data-booking-close]").forEach((button) => {
      button.addEventListener("click", close);
    });
    successModal?.querySelectorAll("[data-booking-success-close]").forEach((button) => {
      button.addEventListener("click", closeSuccess);
    });
    form.addEventListener("submit", handleSubmit);
    getElement("#booking-purpose")?.addEventListener("input", (event) => {
      setText("[data-purpose-count]", String(event.target.value.length));
      updateSummary();
    });
    getElement("#booking-participants")?.addEventListener("input", updateSummary);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        if (!successModal?.hidden) closeSuccess();
        else close();
      }
    });
    document.addEventListener("room-booking:open", (event) => open(event.detail));
  }

  setup();
  window.RoomBookingUI = { open, close, openSuccess };
})();
