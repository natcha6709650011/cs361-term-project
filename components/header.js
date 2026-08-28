const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('.main-nav');
const dropdown = document.querySelector('.nav-dropdown');
const dropdownButton = document.querySelector('.dropdown-toggle');

menuButton.addEventListener('click', () => {
  const isOpen = navigation.classList.toggle('open');
  menuButton.setAttribute('aria-expanded', isOpen);
  menuButton.setAttribute('aria-label', isOpen ? 'ปิดเมนู' : 'เปิดเมนู');
});

dropdownButton.addEventListener('click', () => {
  const isOpen = dropdown.classList.toggle('open');
  dropdownButton.setAttribute('aria-expanded', isOpen);
});

document.addEventListener('click', (event) => {
  if (!dropdown.contains(event.target)) {
    dropdown.classList.remove('open');
    dropdownButton.setAttribute('aria-expanded', 'false');
  }
});
