const ROOMS_API_URL =
  "https://aisw93f81a.execute-api.us-east-1.amazonaws.com/v1/rooms";

const typePage =
  document.body.dataset.roomType ||
  new URLSearchParams(window.location.search).get("type") ||
  "classroom";

const legacyTypePages = {
  activity: "room-activity.html",
  coworking: "room-coworking.html",
  lab: "room-lab.html",
  meeting: "room-meeting.html",
};

// รองรับลิงก์เดิมจากเมนูเวอร์ชันแรก
if (!document.body.dataset.roomType && legacyTypePages[typePage]) {
  window.location.replace(legacyTypePages[typePage]);
}

const MEETING_ROOMS = [
  ["214", 2, 8],
  ["215", 2, 8],
  ["301", 3, 8],
  ["302", 3, 8],
  ["303", 3, 8],
  ["304", 3, 8],
  ["305", 3, 4],
  ["314", 3, 8],
  ["315", 3, 8],
  ["316", 3, 8],
];

const LAB_ROOMS = [
  ["107", 1, 84],
  ["111", 1, 48],
  ["213", 2, 60],
];

const ACTIVITY_ROOMS = [
  ["106", 1, null],
];

const COWORKING_ROOMS = [
  ["307", 3, 32],
  ["313", 3, 54],
];

const searchForm = document.querySelector("#search-form");
const searchInput = document.querySelector("#room-search");
const searchMessage = document.querySelector("#search-message");

if (searchForm) {
  searchForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const keyword = searchInput.value.trim();

    searchMessage.textContent = keyword
      ? `กำลังค้นหา “${keyword}” ในห้องเรียน`
      : "กรุณาระบุชื่อหรือหมายเลขห้อง";
  });
}

// รองรับทั้งรูปแบบ [] และ { data: [] }
function getRoomsList(payload) {
  if (Array.isArray(payload)) return payload;

  return payload?.data ?? payload?.rooms ?? payload?.items ?? [];
}

function getTypeName(room) {
  return (
    room?.room_type?.type_name ??
    room?.room_type ??
    room?.room_type_name ??
    room?.type_name ??
    ""
  );
}

function capacityLabel(capacity) {
  return `
    <svg class="person-icon" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="7" r="3.25"></circle>
      <path d="M5 20c.5-3.8 3-6 7-6s6.5 2.2 7 6"></path>
    </svg>
    ${capacity ?? "-"} ที่นั่ง
  `;
}

// ==============================
// ห้องประชุม
// ==============================

function createMeetingCard([number, floor, capacity]) {
  const card = document.createElement("article");

  card.className = "room-card";

  card.innerHTML = `
    <div class="room-card__image">
      <b>ห้องประชุม</b>
    </div>

    <div class="room-card__detail">
      <h3>บร2-${number}</h3>

      <p>ห้องประชุม ${number} ชั้น ${floor}</p>

      <div class="tags">
        <span>โต๊ะ</span>
        <span>เก้าอี้</span>
        <span>ทีวี</span>
        <span>ปลั๊กไฟ</span>
      </div>

      <footer>
        <span class="capacity">
          ${capacityLabel(capacity)}
        </span>

        <a href="room-detail.html?room=${number}">
          ดูรายละเอียดเพิ่มเติม
        </a>
      </footer>
    </div>
  `;

  return card;
}

// ==============================
// ห้องปฏิบัติการ
// ==============================

function createLabCard([number, floor, capacity]) {
  const card = document.createElement("article");

  card.className = "room-card";

  card.innerHTML = `
    <div class="room-card__image">
      <b>ห้องปฏิบัติการ</b>
    </div>

    <div class="room-card__detail">
      <h3>บร2-${number}</h3>

      <p>ห้องปฏิบัติการ ${number} ชั้น ${floor}</p>

      <div class="tags">
        <span>โต๊ะ</span>
        <span>เก้าอี้</span>
        <span>คอมพิวเตอร์</span>
        <span>โปรเจคเตอร์</span>
      </div>

      <footer>
        <span class="capacity">
          ${capacityLabel(capacity)}
        </span>

        <a href="room-detail.html?room=${number}">
          ดูรายละเอียดเพิ่มเติม
        </a>
      </footer>
    </div>
  `;

  return card;
}

// ==============================
// ห้องกิจกรรม
// ==============================

function createActivityCard([number, floor, capacity]) {
  const card = document.createElement("article");

  card.className = "room-card";

  card.innerHTML = `
    <div class="room-card__image">
      <b>ห้องกิจกรรมนักศึกษา</b>
    </div>

    <div class="room-card__detail">
      <h3>บร2-${number}</h3>

      <p>ห้องกิจกรรม ${number} ชั้น ${floor}</p>

      <div class="tags">
        <span>โต๊ะ</span>
        <span>เก้าอี้</span>
      </div>

      <footer>
        <span class="capacity">
          ${capacityLabel(capacity)}
        </span>

        <a href="room-detail.html?room=${number}">
          ดูรายละเอียดเพิ่มเติม
        </a>
      </footer>
    </div>
  `;

  return card;
}

// ==============================
// Co-Working Space
// ==============================

function createCoworkingCard([number, floor, capacity]) {
  const card = document.createElement("article");

  card.className = "room-card";

  card.innerHTML = `
    <div class="room-card__image">
      <b>Co-Working Space</b>
    </div>

    <div class="room-card__detail">
      <h3>บร2-${number}</h3>

      <p>Co-Working Space ${number} ชั้น ${floor}</p>

      <div class="tags">
        <span>โต๊ะ</span>
        <span>เก้าอี้</span>
        <span>ปลั๊กไฟ</span>
      </div>

      <footer>
        <span class="capacity">
          ${capacityLabel(capacity)}
        </span>

        <a href="room-detail.html?room=${number}">
          ดูรายละเอียดเพิ่มเติม
        </a>
      </footer>
    </div>
  `;

  return card;
}

// ==============================
// หน้า Meeting
// ==============================

function setMeetingPage() {
  if (typePage !== "meeting") return;

  document.title = "ห้องประชุม | CS Thammasat";

  document.querySelector(".type-hero h1").textContent =
    "ห้องประชุม";

  document.querySelector(".type-hero__image").style.backgroundImage =
    "url('assets/bor2-214.jpg')";

  document.querySelector(".room-list h2").textContent =
    "ห้องประชุม";

  document.querySelector("#room-count").textContent =
    `จำนวน ${MEETING_ROOMS.length} ห้อง`;

  const roomList = document.querySelector(".room-list");
  const grid = document.querySelector("#room-list-grid");

  roomList.classList.add("room-list--meeting");

  grid.replaceChildren(
    ...MEETING_ROOMS.map(createMeetingCard)
  );
}

// ==============================
// หน้า Lab
// ==============================

function setLabPage() {
  if (typePage !== "lab") return;

  document.title =
    "ห้องปฏิบัติการคอมพิวเตอร์ | CS Thammasat";

  document.querySelector(".type-hero h1").textContent =
    "ห้องปฏิบัติการคอมพิวเตอร์";

  document.querySelector(".type-hero__image").style.backgroundImage =
    "url('assets/bor2-107.jpg')";

  document.querySelector(".room-list h2").textContent =
    "ห้องปฏิบัติการคอมพิวเตอร์";

  document.querySelector("#room-count").textContent =
    `จำนวน ${LAB_ROOMS.length} ห้อง`;

  const roomList = document.querySelector(".room-list");
  const grid = document.querySelector("#room-list-grid");

  roomList.classList.add("room-list--lab");

  grid.replaceChildren(
    ...LAB_ROOMS.map(createLabCard)
  );
}

// ==============================
// หน้า Activity
// ==============================

function setActivityPage() {
  if (typePage !== "activity") return;

  document.title =
    "ห้องกิจกรรมนักศึกษา | CS Thammasat";

  document.querySelector(".type-hero h1").textContent =
    "ห้องกิจกรรมนักศึกษา";

  document.querySelector(".type-hero__image").style.backgroundImage =
    "url('assets/bor2-106.jpg')";

  document.querySelector(".room-list h2").textContent =
    "ห้องกิจกรรมนักศึกษา";

  document.querySelector("#room-count").textContent =
    `จำนวน ${ACTIVITY_ROOMS.length} ห้อง`;

  const roomList = document.querySelector(".room-list");
  const grid = document.querySelector("#room-list-grid");

  roomList.classList.add("room-list--activity");

  grid.replaceChildren(
    ...ACTIVITY_ROOMS.map(createActivityCard)
  );
}

// ==============================
// หน้า Co-Working
// ==============================

function setCoworkingPage() {
  if (typePage !== "coworking") return;

  document.title =
    "Co-Working Space | CS Thammasat";

  document.querySelector(".type-hero h1").textContent =
    "Co-Working Space";

  document.querySelector(".type-hero__image").style.backgroundImage =
    "url('assets/coworking-space.jpg')";

  document.querySelector(".room-list h2").textContent =
    "Co-Working Space";

  document.querySelector("#room-count").textContent =
    `จำนวน ${COWORKING_ROOMS.length} ห้อง`;

  const roomList = document.querySelector(".room-list");
  const grid = document.querySelector("#room-list-grid");

  roomList.classList.add("room-list--coworking");

  grid.replaceChildren(
    ...COWORKING_ROOMS.map(createCoworkingCard)
  );
}

// ==============================
// โหลด API
// ==============================

async function loadClassrooms() {
  try {
    const response = await fetch(ROOMS_API_URL, {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const selectedRooms = getRoomsList(
      await response.json()
    ).filter(
      (room) =>
        getTypeName(room) ===
        (
          {
            meeting: "ห้องประชุม",
            lab: "ห้องปฏิบัติการคอมพิวเตอร์",
            activity: "ห้องกิจกรรมนักศึกษา",
            coworking: "Co-Working Space",
          }[typePage] ?? "ห้องเรียน"
        )
    );

    console.info(
      `พบข้อมูล${getTypeName(selectedRooms[0]) || "ห้อง"}จาก API`,
      selectedRooms.length,
      "ห้อง"
    );

  } catch (error) {
    console.warn(
      "ไม่สามารถโหลดรายการห้องเรียนจาก API ได้ จึงแสดงข้อมูลตัวอย่างแทน",
      error
    );
  }
}

// ==============================
// เริ่มทำงาน
// ==============================

setMeetingPage();
setLabPage();
setActivityPage();
setCoworkingPage();

// เปลี่ยนสัญลักษณ์ตัวอักษรเดิมในหน้า classroom เป็นไอคอนรูปคน
document.querySelectorAll(".capacity").forEach((capacity) => {
  if (!capacity.querySelector(".person-icon")) {
    const text = capacity.textContent
      .replace("♙", "")
      .replace("ที่นั่ง", "")
      .trim();

    capacity.innerHTML = capacityLabel(text);
  }
});

loadClassrooms();