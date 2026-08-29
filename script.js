const ROOMS_API_URL = 'https://aisw93f81a.execute-api.us-east-1.amazonaws.com/v1/rooms';
const ROOM_PHOTOS = {
  '106': 'assets/bor2-106.jpg',
  '107': 'assets/bor2-107.jpg',
  '214': 'assets/bor2-214.jpg',
  '308': 'assets/bor2-308.jpg',
};
const RECOMMENDED_ROOM_NUMBERS = ['308', '107', '214', '106'];

const personIcon = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="7" r="3.5"/><path d="M5 21c.5-4.2 3-6.5 7-6.5s6.5 2.3 7 6.5"/></svg>';

// ปุ่มรายละเอียดที่ยังไม่มีหน้ารายละเอียดของห้องนั้น จะไม่เปลี่ยน hash หรือเลื่อนหน้าจอ
document.addEventListener('click', (event) => {
  const link = event.target.closest('.room-detail footer a:not(.room-detail-link)');
  if (link) event.preventDefault();
});

// ไม่ให้เบราว์เซอร์จำตำแหน่งเลื่อนเดิมหรือ hash เดิมเมื่อรีเฟรชหน้า Home
if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
const resetHomeScroll = () => {
  if (window.location.hash) history.replaceState(null, '', window.location.pathname);
  window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
};
window.addEventListener('DOMContentLoaded', resetHomeScroll);
window.addEventListener('load', resetHomeScroll);
window.addEventListener('pageshow', resetHomeScroll);

document.querySelector('#search-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const query = document.querySelector('#room-search').value.trim();
  const message = document.querySelector('#search-message');
  message.textContent = query ? `กำลังค้นหา “${query}” (ตัวอย่างหน้าแรก)` : 'กรุณาระบุชื่อหรือหมายเลขห้อง';
});

function getRoomsList(payload) {
  if (Array.isArray(payload)) return payload;
  return payload?.data ?? payload?.rooms ?? payload?.items ?? [];
}

function getRoomType(room) {
  return room.room_type?.type_name
    ?? room.room_type_name
    ?? room.type_name
    ?? (typeof room.room_type === 'string' ? room.room_type : null)
    ?? 'ห้อง';
}

function getAmenities(value) {
  let amenities = value;
  if (typeof amenities === 'string') {
    try { amenities = JSON.parse(amenities); } catch { amenities = []; }
  }
  if (!Array.isArray(amenities)) return [];
  return amenities.map((amenity) => {
    if (typeof amenity === 'string') return amenity;
    const item = amenity?.item ?? amenity?.name ?? amenity?.label;
    const quantity = amenity?.qty ?? amenity?.quantity;
    return item ? `${item}${quantity ? ` ${quantity}` : ''}` : null;
  }).filter(Boolean);
}

function roomNumber(room) {
  return String(room.room_number ?? room.number ?? room.room_no ?? 'ไม่ระบุ');
}

function roomLabel(number) {
  return /^[0-9]+$/.test(number) ? `บร2-${number}` : number;
}

function createRoomCard(room) {
  const number = roomNumber(room);
  const type = getRoomType(room);
  const floor = room.floor ?? null;
  const capacity = room.capacity ?? null;
  const amenities = getAmenities(room.amenities_json ?? room.amenities).slice(0, 4);
  const numberKey = number.match(/\d+$/)?.[0] ?? number;
  const photo = ROOM_PHOTOS[numberKey];
  const article = document.createElement('article');
  article.className = 'room-card';

  const image = document.createElement('div');
  image.className = `room-image${photo ? '' : ' room-image-fallback'}`;
  if (photo) image.style.background = `url("${photo}") center 58% / cover no-repeat`;
  const badge = document.createElement('b');
  badge.textContent = type;
  image.append(badge);

  const detail = document.createElement('div');
  detail.className = 'room-detail';
  const title = document.createElement('h3');
  title.textContent = roomLabel(number);
  const location = document.createElement('p');
  location.textContent = floor === null ? `${type} ${number}` : `${type} ${number} ชั้น ${floor}`;
  const tags = document.createElement('div');
  tags.className = 'tags';
  (amenities.length ? amenities : ['ยังไม่มีข้อมูลอุปกรณ์']).forEach((amenity) => {
    const tag = document.createElement('span');
    tag.textContent = amenity;
    tags.append(tag);
  });

  const footer = document.createElement('footer');
  const capacityText = document.createElement('span');
  capacityText.className = 'capacity';
  capacityText.innerHTML = `${personIcon}${capacity === null ? 'ไม่ระบุความจุ' : `${capacity} ที่นั่ง`}`;
  const detailLink = document.createElement('a');
  detailLink.className = 'room-detail-link';
  detailLink.href = `room-detail.html?room=${encodeURIComponent(numberKey)}`;
  detailLink.textContent = 'ดูรายละเอียดเพิ่มเติม';
  footer.append(capacityText, detailLink);
  detail.append(title, location, tags, footer);
  article.append(image, detail);
  return article;
}

async function loadRoomsFromApi() {
  const grid = document.querySelector('#rooms-grid');
  if (!grid) return;
  const fallbackCards = new Map(
    [...grid.children].map((card) => [card.querySelector('h3')?.textContent.match(/\d+$/)?.[0], card]),
  );
  try {
    const response = await fetch(ROOMS_API_URL, { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const rooms = getRoomsList(await response.json());
    if (!Array.isArray(rooms) || rooms.length === 0) throw new Error('ไม่มีข้อมูลห้องใน API');
    const roomsByNumber = new Map(
      rooms.map((room) => [roomNumber(room).match(/\d+$/)?.[0], room]),
    );
    // หน้า Home ใช้ชุดห้องแนะนำตามแบบเสมอ ไม่ใช่ 4 รายการแรกที่ Mock API ส่งมา
    const recommendedCards = RECOMMENDED_ROOM_NUMBERS.map((number) => {
      const apiRoom = roomsByNumber.get(number);
      return apiRoom ? createRoomCard(apiRoom) : fallbackCards.get(number)?.cloneNode(true);
    }).filter(Boolean);
    grid.replaceChildren(...recommendedCards);
  } catch (error) {
    // หน้าเว็บยังใช้ข้อมูล fallback ใน index.html ได้ หาก Mock API ยังไม่เปิด CORS หรือเชื่อมต่อไม่ได้
    console.warn('ไม่สามารถโหลดข้อมูลห้องจาก API ได้ จึงแสดงข้อมูลตัวอย่างแทน', error);
  }
}

loadRoomsFromApi();
