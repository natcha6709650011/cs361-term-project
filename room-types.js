const ROOMS_API_URL =
  "https://7i1mw8hw5l.execute-api.us-east-1.amazonaws.com/v1/rooms";

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

const pageTypes = {
  classroom: "ห้องเรียน",
  meeting: "ห้องประชุม",
  lab: "ห้องปฏิบัติการคอมพิวเตอร์",
  activity: "ห้องกิจกรรมนักศึกษา",
  coworking: "Co-Working Space",
};

const typeDestinations = {
  ห้องเรียน: "room-types.html",
  ห้องประชุม: "room-meeting.html",
  ห้องปฏิบัติการ: "room-lab.html",
  ห้องปฏิบัติการคอมพิวเตอร์: "room-lab.html",
  ห้องแลป: "room-lab.html",
  ห้องกิจกรรม: "room-activity.html",
  ห้องกิจกรรมนักศึกษา: "room-activity.html",
  coworkingspace: "room-coworking.html",
  coworking: "room-coworking.html",
  โคเวิร์กกิงสเปซ: "room-coworking.html",
};

const searchForm = document.querySelector("#search-form");
const searchInput = document.querySelector("#room-search");
const searchMessage = document.querySelector("#search-message");
const roomGrid = document.querySelector("#room-list-grid");
const roomCount = document.querySelector("#room-count");
let allRooms = [];

// รองรับลิงก์เดิมจากเมนูเวอร์ชันแรก
if (!document.body.dataset.roomType && legacyTypePages[typePage]) {
  window.location.replace(legacyTypePages[typePage]);
}

function normalizeSearchText(value) {
  return String(value ?? "")
    .toLowerCase()
    .replace(/\s+/g, "")
    .replace(/[\-–—]/g, "");
}

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

function getAmenities(room) {
  const rawAmenities = room?.amenities_json ?? room?.amenities ?? [];

  try {
    const amenities =
      typeof rawAmenities === "string"
        ? JSON.parse(rawAmenities)
        : rawAmenities;
    return Array.isArray(amenities)
      ? amenities
          .map((amenity) => amenity?.item ?? amenity?.name ?? amenity)
          .filter(Boolean)
      : [];
  } catch {
    return [];
  }
}

function capacityLabel(capacity) {
  return `
    <svg class="person-icon" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="7" r="3.25"></circle>
      <path d="M5 20c.5-3.8 3-6 7-6s6.5 2.2 7 6"></path>
    </svg>
    ${capacity ?? "ไม่ระบุ"} ${capacity ? "ที่นั่ง" : ""}
  `;
}

function createRoomCard(room) {
  const number = room.room_number ?? room.roomNumber;
  const typeName = getTypeName(room);
  const floor = room.floor ?? "-";
  const amenities = getAmenities(room);
  const card = document.createElement("article");
  const image = document.createElement("div");
  const detail = document.createElement("div");

  card.className = "room-card";
  image.className = "room-card__image";
  detail.className = "room-card__detail";

  if (room.image_url) image.style.backgroundImage = `url("${room.image_url}")`;

  const badge = document.createElement("b");
  badge.textContent = typeName;
  image.append(badge);

  const heading = document.createElement("h3");
  heading.textContent = `บร2-${number}`;
  const location = document.createElement("p");
  location.textContent = `${typeName} ${number} ชั้น ${floor}`;
  const tags = document.createElement("div");
  tags.className = "tags";
  amenities.forEach((amenity) => {
    const tag = document.createElement("span");
    tag.textContent = amenity;
    tags.append(tag);
  });

  const footer = document.createElement("footer");
  const capacity = document.createElement("span");
  capacity.className = "capacity";
  capacity.innerHTML = capacityLabel(room.capacity);
  const link = document.createElement("a");
  link.href = `room-detail.html?room=${encodeURIComponent(number)}`;
  link.textContent = "ดูรายละเอียดเพิ่มเติม";
  footer.append(capacity, link);
  detail.append(heading, location, tags, footer);
  card.append(image, detail);
  return card;
}

function roomsForCurrentPage() {
  const expectedType = pageTypes[typePage] ?? pageTypes.classroom;
  return allRooms.filter((room) => getTypeName(room) === expectedType);
}

function renderRooms(rooms) {
  if (!roomGrid) return;
  roomGrid.replaceChildren(...rooms.map(createRoomCard));
  if (roomCount) roomCount.textContent = `จำนวน ${rooms.length} ห้อง`;
}

function filterVisibleRoomCards(keyword) {
  const normalizedKeyword = normalizeSearchText(keyword);
  const cards = [...document.querySelectorAll("#room-list-grid .room-card")];
  const matchedCards = cards.filter((card) => {
    const matches =
      !normalizedKeyword ||
      normalizeSearchText(card.textContent).includes(normalizedKeyword);
    card.hidden = !matches;
    return matches;
  });

  if (roomCount)
    roomCount.textContent = normalizedKeyword
      ? `พบ ${matchedCards.length} ห้อง`
      : `จำนวน ${cards.length} ห้อง`;
  if (searchMessage) {
    searchMessage.textContent = normalizedKeyword
      ? matchedCards.length
        ? `พบห้องที่ตรงกับ “${keyword}” ${matchedCards.length} ห้อง`
        : `ไม่พบห้องที่ตรงกับ “${keyword}”`
      : "แสดงห้องทั้งหมด";
  }
}

async function loadRooms() {
  if (!roomGrid) return;

  try {
    const response = await fetch(ROOMS_API_URL, {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    allRooms = getRoomsList(await response.json());
    renderRooms(roomsForCurrentPage());
  } catch (error) {
    console.warn("ไม่สามารถโหลดรายการห้องจาก API ได้", error);
    if (searchMessage)
      searchMessage.textContent =
        "ไม่สามารถโหลดข้อมูลห้องได้ กรุณาลองใหม่อีกครั้ง";
  }
}

if (searchForm) {
  searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const keyword = searchInput.value.trim();
    const normalizedKeyword = normalizeSearchText(keyword);
    const availabilityKeywords = [
      "ห้องว่าง",
      "ค้นหาห้องว่าง",
      "เช็คห้องว่าง",
      "เช็กห้องว่าง",
    ];

    if (availabilityKeywords.includes(normalizedKeyword)) {
      window.location.href = "room-search.html";
      return;
    }

    const typeDestination = typeDestinations[normalizedKeyword];
    if (typeDestination) {
      window.location.href = typeDestination;
      return;
    }

    const roomNumber = keyword.match(/\d{3}/)?.[0];
    const matchedRoom = allRooms.find(
      (room) => String(room.room_number) === roomNumber,
    );
    if (matchedRoom) {
      const roomDestination =
        typeDestinations[normalizeSearchText(getTypeName(matchedRoom))];
      const currentPage =
        window.location.pathname.split("/").pop() || "room-types.html";
      if (roomDestination && roomDestination !== currentPage) {
        window.location.href = roomDestination;
        return;
      }
    }

    filterVisibleRoomCards(keyword);
  });
}

loadRooms();
