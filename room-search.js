const form = document.querySelector('#availability-search-form');
const searchDate = document.querySelector('#search-date');
const searchTime = document.querySelector('#start-time');
const endTime = document.querySelector('#end-time');
const minCapacity = document.querySelector('#min-capacity');
const roomType = document.querySelector('#room-type');
const amenityInputs = document.querySelectorAll('input[name="amenities"]');
const validationMessage = document.querySelector('#search-validation');
const searchLoading = document.querySelector('#search-loading');
const searchEmpty = document.querySelector('#search-empty');
const searchError = document.querySelector('#search-error');
const searchResults = document.querySelector('#search-results');
const roomCardTemplate = document.querySelector('#room-card-template');
const resultCount = document.querySelector('#result-count');
let searchTimer;
let latestSearchId = 0;

function hideSearchStates() {
    searchLoading.hidden = true;
    searchEmpty.hidden = true;
    searchError.hidden = true;
}
function showLoading(){
    hideSearchStates();
    searchLoading.hidden = false;
    resultCount.textContent = 'กำลังค้นหาห้องว่าง...';
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
    const hasAmenities = [...amenityInputs].some((input) => input.checked);

    // ต้องมี filter อย่างน้อย 1 ตัว
    if (!hasDate && !hasStartTime && !hasEndTime && !hasCapacity && !hasRoomType && !hasAmenities) {
        showValidationMessage("กรุณาเลือกเงื่อนไขการค้นหาอย่างน้อย 1 รายการ");
        return false;
    }

    // ถ้าเลือกเวลา ต้องเลือกทั้งเริ่มและสิ้นสุดให้ครบ
    if (hasStartTime !== hasEndTime) {
        showValidationMessage("กรุณาเลือกเวลาเริ่มและเวลาสิ้นสุดให้ครบ");
        return false;
    }

    if (hasStartTime && searchTime.value >= endTime.value) {
        showValidationMessage("เวลาสิ้นสุดต้องมากกว่าเวลาเริ่มต้น");
        return false;
    }

    return true;
}

function clearSearchResults() {
    hideSearchStates();
    clearValidation();
    searchResults.innerHTML = '';
    resultCount.textContent = 'เลือกเงื่อนไขแล้วระบบจะแสดงห้องว่างให้ทันที';
}

async function searchRooms() {
    const searchId = ++latestSearchId;

    const hasSearchCriteria = searchDate.value || searchTime.value || endTime.value
        || minCapacity.value || roomType.value
        || [...amenityInputs].some((input) => input.checked);

    if (!hasSearchCriteria) {
        clearSearchResults();
        return;
    }

    if (!validateSearchForm()) {
        searchResults.innerHTML = '';
        resultCount.textContent = 'กรุณาตรวจสอบเงื่อนไขการค้นหา';
        return;
    }

    const searchParams = {
        date: searchDate.value,
        startTime: searchTime.value,
        endTime: endTime.value,
        minCapacity: minCapacity.value,
        roomType: roomType.value,
        amenities: [...amenityInputs]
            .filter((input) => input.checked)
            .map((input) => input.value),
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

    if (searchParams.amenities.length) {
        query.append('amenities', searchParams.amenities.join(','));
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

            if (searchId === latestSearchId) {
                hideSearchStates();
            }
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

        // หากผู้ใช้เปลี่ยนเงื่อนไขระหว่างรอผล ให้ใช้ผลของการค้นหาล่าสุดเท่านั้น
        if (searchId !== latestSearchId) {
            return;
        }

        console.log('API response:', data);

        if (!response.ok) {
            throw new Error(
                data.message || 'เกิดข้อผิดพลาดในการค้นหาห้อง'
            );
        }

        if (!data.rooms || data.rooms.length === 0) {
            searchResults.innerHTML = '';
            resultCount.textContent = 'ไม่พบห้องว่างตามเงื่อนไขที่เลือก';
            showEmpty();
            return;
        }

        hideSearchStates();

        console.log('Available rooms:', data.rooms);
        renderRooms(data.rooms);
        resultCount.textContent = `พบห้องว่าง ${data.rooms.length} ห้อง`;

    } catch (error) {
        if (searchId !== latestSearchId) {
            return;
        }
        console.error('Search error:', error);
        searchResults.innerHTML = '';
        resultCount.textContent = 'ไม่สามารถค้นหาห้องว่างได้';
        hideSearchStates();
        searchError.hidden = false;
    }
}

function queueSearch() {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(searchRooms, 300);
}

form.addEventListener('submit', (event) => {
    event.preventDefault();
    window.clearTimeout(searchTimer);
    searchRooms();
});

form.addEventListener('change', (event) => {
    const isSearchControl = event.target.matches(
        '#search-date, #start-time, #end-time, #min-capacity, #room-type, input[name="amenities"]'
    );

    if (isSearchControl) {
        queueSearch();
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
