/* Temporary V3 data. Replace this source with GET /bookings/me after API is ready. */
window.MY_BOOKINGS_MOCK = [
  { id: "booking-1", date: "2026-10-30", startTime: "16:30", endTime: "18:00", room: "บร.2-308", roomType: "ห้องเรียน", purpose: "จัดประชุมสาขาวิชา", participants: 50, status: "PENDING" },
  { id: "booking-2", date: "2026-10-28", startTime: "13:30", endTime: "16:30", room: "บร.2-310", roomType: "ห้องเรียน", purpose: "สัมมนา", participants: 40, status: "APPROVED" },
  { id: "booking-3", date: "2026-10-25", startTime: "09:00", endTime: "12:00", room: "บร.2-309", roomType: "ห้องเรียน", purpose: "ประชุมกลุ่ม", participants: 20, status: "CANCELLED" },
  { id: "booking-4", date: "2026-10-20", startTime: "09:00", endTime: "12:00", room: "บร.2-308", roomType: "ห้องเรียน", purpose: "จัดกิจกรรมชมรม", participants: 60, status: "APPROVED" },
  { id: "booking-5", date: "2026-10-15", startTime: "13:30", endTime: "15:00", room: "บร.2-310", roomType: "ห้องเรียน", purpose: "ทดลองระบบ", participants: 30, status: "REJECTED", rejectionReason: "ห้องถูกจัดไว้สำหรับการเรียนการสอน" },
];

/* Temporary availability data. Replace with a backend 409 Conflict response. */
window.MY_BOOKING_CONFLICTS = [
  { room: "บร.2-308", date: "2026-10-30", startTime: "13:30", endTime: "15:00", source: "FACILITY_SCHEDULE" },
];
