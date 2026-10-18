/*
 * Booking API boundary for V3.
 *
 * The application starts in mock mode because the authenticated Booking API
 * contract is not available yet. Once it is ready, set
 * window.BOOKING_API_CONFIG = { mode: "api", baseUrl, getAccessToken }
 * before this script and keep UI files unchanged.
 */
(function bookingService() {
  const config = window.BOOKING_API_CONFIG || { mode: "mock" };
  let mockBookings = null;

  class BookingServiceError extends Error {
    constructor(message, { code = "BOOKING_ERROR", status = 0, details = null } = {}) {
      super(message);
      this.name = "BookingServiceError";
      this.code = code;
      this.status = status;
      this.details = details;
    }
  }

  const clone = (value) => JSON.parse(JSON.stringify(value));
  const wait = (milliseconds = 250) => new Promise((resolve) => window.setTimeout(resolve, milliseconds));

  function getMockBookings() {
    if (mockBookings === null) {
      if (!Array.isArray(window.MY_BOOKINGS_MOCK)) {
        throw new BookingServiceError("Mock booking data is unavailable", { code: "DATA_UNAVAILABLE" });
      }
      mockBookings = clone(window.MY_BOOKINGS_MOCK);
    }
    return mockBookings;
  }

  function roomKey(value) {
    return String(value ?? "").replace(/[^0-9a-z]/gi, "").toLowerCase();
  }

  function timesOverlap(startA, endA, startB, endB) {
    return startA < endB && endA > startB;
  }

  function findMockConflict({ id, room, date, startTime, endTime }) {
    const activeBookings = getMockBookings().filter((booking) =>
      booking.id !== id &&
      ["PENDING", "APPROVED"].includes(booking.status),
    );
    const fixedSchedules = Array.isArray(window.MY_BOOKING_CONFLICTS) ? window.MY_BOOKING_CONFLICTS : [];

    return [...activeBookings, ...fixedSchedules].find((item) =>
      roomKey(item.room) === roomKey(room) &&
      item.date === date &&
      timesOverlap(startTime, endTime, item.startTime, item.endTime),
    ) || null;
  }

  function unwrap(payload, key) {
    return payload?.[key] ?? payload?.data?.[key] ?? payload?.data ?? payload;
  }

  async function apiRequest(path, options = {}) {
    if (!config.baseUrl || typeof config.getAccessToken !== "function") {
      throw new BookingServiceError("Booking API configuration is incomplete", { code: "AUTH_NOT_READY" });
    }

    const token = await config.getAccessToken();
    if (!token) throw new BookingServiceError("Please sign in again", { code: "AUTH_REQUIRED", status: 401 });

    const response = await fetch(`${config.baseUrl}${path}`, {
      ...options,
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${token}`,
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });

    const payload = await response.json().catch(() => ({}));
    if (response.status === 409) {
      throw new BookingServiceError("Selected time is unavailable", {
        code: "BOOKING_CONFLICT",
        status: 409,
        details: payload,
      });
    }
    if (!response.ok) {
      throw new BookingServiceError(payload?.message || "Booking request failed", {
        code: "BOOKING_REQUEST_FAILED",
        status: response.status,
        details: payload,
      });
    }
    return payload;
  }

  async function getMyBookings() {
    if (config.mode === "api") {
      const payload = await apiRequest("/bookings/me");
      const bookings = unwrap(payload, "bookings");
      return Array.isArray(bookings) ? bookings : [];
    }

    await wait();
    return clone(getMockBookings());
  }

  async function createBooking(payload) {
    if (config.mode === "api") {
      const response = await apiRequest("/bookings", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      return { success: true, booking: unwrap(response, "booking") };
    }

    await wait();
    return { isMock: true };
  }

  async function updateBooking(id, payload) {
    if (config.mode === "api") {
      const response = await apiRequest(`/bookings/${encodeURIComponent(id)}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      return { booking: unwrap(response, "booking") };
    }

    await wait();
    const booking = getMockBookings().find((item) => item.id === id);
    if (!booking) throw new BookingServiceError("Booking was not found", { code: "NOT_FOUND", status: 404 });

    const conflict = findMockConflict({ id, room: booking.room, ...payload });
    if (conflict) {
      throw new BookingServiceError("Selected time is unavailable", {
        code: "BOOKING_CONFLICT",
        status: 409,
        details: { conflict },
      });
    }

    Object.assign(booking, payload);
    return { booking: clone(booking), isMock: true };
  }

  async function cancelBooking(id) {
    if (config.mode === "api") {
      const response = await apiRequest(`/bookings/${encodeURIComponent(id)}`, { method: "DELETE" });
      return { booking: unwrap(response, "booking") };
    }

    await wait();
    const booking = getMockBookings().find((item) => item.id === id);
    if (!booking) throw new BookingServiceError("Booking was not found", { code: "NOT_FOUND", status: 404 });

    booking.status = "CANCELLED";
    return { booking: clone(booking), isMock: true };
  }

  window.BookingService = { getMyBookings, createBooking, updateBooking, cancelBooking, BookingServiceError };
})();
