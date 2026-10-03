const form = document.querySelector('#room-search-form');

const searchDate = document.querySelector('#search-date');
const searchTime = document.querySelector('#search-time');
const endTime = document.querySelector('#end-time');
const minCapacity = document.querySelector('#min-capacity');
const roomType = document.querySelector('#room-type');

const validationMessage = document.querySelector('#search-validation-message');

const searchLoading = document.querySelector('#search-loading');
const searchEmpty = document.querySelector('#search-empty');
const searchError = document.querySelector('#search-error');
const searchResults = document.querySelector('#search-results');

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
        showValidation("กรุณาเลือกวันที่");
        return false;
    }
    if(!searchTime.value){
        showValidation("กรุณาเลือกเวลาเริ่มต้น");
        return false;
    }
    if(!endTime.value){
        showValidation("กรุณาเลือกเวลาสิ้นสุด");
        return false;
    }
    if(!minCapacity.value){
        showValidation("กรุณาเลือกความจุขั้นต่ำ");
        return false;
    }
    if(startTime.value >= endTime.value){
        showValidation("เวลาสิ้นสุดต้องมากกว่าเวลาเริ่มต้น");
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
});