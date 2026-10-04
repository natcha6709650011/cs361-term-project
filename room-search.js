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
function validateSearchForm(){
    clearValidation();

    if(!searchDate.value){
        showValidationMessage("กรุณาเลือกวันที่");
        return false;
    }
    if(!searchTime.value){
        showValidationMessage("กรุณาเลือกเวลาเริ่มต้น");
        return false;
    }
    if(!endTime.value){
        showValidationMessage("กรุณาเลือกเวลาสิ้นสุด");
        return false;
    }
    if(!minCapacity.value){
        showValidationMessage("กรุณาเลือกความจุขั้นต่ำ");
        return false;
    }
    if(searchTime.value >= endTime.value){
        showValidationMessage("เวลาสิ้นสุดต้องมากกว่าเวลาเริ่มต้น");
        return false;
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
    
    const query = new URLSearchParams({
        date: searchParams.date,
        startTime: searchParams.startTime,
        endTime: searchParams.endTime,
        minCapacity: searchParams.minCapacity,
        roomType: searchParams.roomType,
    });

    try {
        const response = await fetch(
            `https://7i1mw8hw5l.execute-api.us-east-1.amazonaws.com/v1/rooms/available?${query.toString()}`
        );

        const data = await response.json();

        console.log('API response:', data);

        if (!response.ok) {
            throw new Error(data.message || 'เกิดข้อผิดพลาดในการค้นหาห้อง');
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
        link.href = `room-detail.html?roomId=${room.room_number}`;

        searchResults.appendChild(card);
    });
}