const form = document.querySelector('#availability-search-form');
const searchDate = document.querySelector('#search-date');
const searchTime = document.querySelector('#start-time');
const endTime = document.querySelector('#end-time');
const minCapacity = document.querySelector('#min-capacity');
const roomType = document.querySelector('#room-type');
const validationMessage = document.querySelector('#search-validation');
const searchLoading = document.querySelector('#search-loading');
const searchEmpty = document.querySelector('#search-empty');
const searchError = document.querySelector('#search-error');
const searchResults = document.querySelector('#search-results');
const roomCardTemplate = document.querySelector('#room-card-template');

function hideSearchStates() {
    searchLoading.hidden = true;
    searchEmpty.hidden = true;
    searchError.hidden = true;
}
function showLoading(){
    hideSearchStates();
    searchLoading.hidden = false;
}
function showEmpty(){
    hideSearchStates();
    searchEmpty.hidden = false;
}
function showValidationMessage(message){
    validationMessage.textContent = message;
    validationMessage.hidden = false;
}
function clearValidation(){
    validationMessage.textContent = '';
    validationMessage.hidden = true;
}
function validateSearchForm() {
    clearValidation();

    const hasDate = !!searchDate.value;
    const hasStartTime = !!searchTime.value;
    const hasEndTime = !!endTime.value;
    const hasCapacity = !!minCapacity.value;
    const hasRoomType = !!roomType.value;

    // ต้องมี filter อย่างน้อย 1 ตัว
    if (!hasDate && !hasStartTime && !hasEndTime && !hasCapacity && !hasRoomType) {
        showValidationMessage("กรุณาเลือกเงื่อนไขการค้นหาอย่างน้อย 1 รายการ");
        return false;
    }

    // ถ้าเลือกเวลา ต้องเลือกเวลาเริ่มและเวลาสิ้นสุดให้ถูกต้อง
    if (hasStartTime && hasEndTime) {
        if (searchTime.value >= endTime.value) {
            showValidationMessage("เวลาสิ้นสุดต้องมากกว่าเวลาเริ่มต้น");
            return false;
        }
    }

    return true;
}

form.addEventListener('submit', async (event) => {
    event.preventDefault();

    if (!validateSearchForm()) {
        return;
    }

    const searchParams = {
        date: searchDate.value,
        startTime: searchTime.value,
        endTime: endTime.value,
        minCapacity: minCapacity.value,
        roomType: roomType.value,
    };

    console.log('Searching rooms with params:', searchParams);

    showLoading();

    // สร้าง query เฉพาะค่าที่ผู้ใช้เลือก
    const query = new URLSearchParams();

    if (searchParams.date) {
        query.append('date', searchParams.date);
    }

    if (searchParams.startTime) {
        query.append('startTime', searchParams.startTime);
    }

    if (searchParams.endTime) {
        query.append('endTime', searchParams.endTime);
    }

    if (searchParams.minCapacity) {
        query.append('minCapacity', searchParams.minCapacity);
    }

    if (searchParams.roomType) {
        query.append('roomType', searchParams.roomType);
    }

    try {
        const isLoggedIn = window.localStorage.getItem('isLoggedIn') === 'true';

        if (!isLoggedIn) {
            const goLogin = confirm(
                'กรุณาเข้าสู่ระบบก่อนค้นหาห้องว่าง\n\nต้องการไปหน้าเข้าสู่ระบบหรือไม่?'
            );

            if (goLogin) {
                window.location.href = 'login.html';
            }

            hideSearchStates();
            return;
        }

        const apiBaseUrl = window.location.port === '5501'
            ? '/api/v1'
            : 'https://7i1mw8hw5l.execute-api.us-east-1.amazonaws.com/v1';

        const response = await fetch(
            `${apiBaseUrl}/rooms/available?${query.toString()}`,
            {
                credentials: 'include',
            }
        );

        const data = await response.json();

        console.log('API response:', data);

        if (!response.ok) {
            throw new Error(
                data.message || 'เกิดข้อผิดพลาดในการค้นหาห้อง'
            );
        }

        if (!data.rooms || data.rooms.length === 0) {
            showEmpty();
            return;
        }

        hideSearchStates();

        console.log('Available rooms:', data.rooms);
        renderRooms(data.rooms);

    } catch (error) {
        console.error('Search error:', error);
        hideSearchStates();
        searchError.hidden = false;
    }
});

function renderRooms(rooms){
    searchResults.innerHTML = '';
    rooms.forEach(room => {
        const card = roomCardTemplate.content.cloneNode(true);
        
        card.querySelector('[data-room-number]').textContent = `บร.2-${room.room_number}`;
        card.querySelector('[data-room-type]').textContent = room.room_type;
        card.querySelector('[data-room-location]').textContent = `ชั้น ${room.floor}`;
        card.querySelector('[data-room-capacity]').textContent = `${room.capacity} คน`;

        const image = card.querySelector('[data-room-image]');
        image.src = room.image_url;
        image.alt = `ห้อง ${room.room_number}`;

        const facilities = card.querySelector('[data-room-facilities]');
        facilities.textContent = Array.isArray(room.amenities)
        ? room.amenities.map(item => item.item).join(', ')
    : '';
        const link = card.querySelector('[data-room-link]');
        link.href = `room-detail.html?roomId=${room.room_number}&date=${searchDate.value}`;

        searchResults.appendChild(card);
    });
}
