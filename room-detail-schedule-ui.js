// UI ของวันที่ในตารางห้อง: เมื่อ API พร้อม ให้ฟัง change จาก #schedule-date
document.querySelectorAll("[data-schedule-date-picker]").forEach((picker) => {
  const source = picker.querySelector(".schedule-date-source");
  const trigger = picker.querySelector(".schedule-date-trigger");
  const triggerText = trigger.querySelector("span");
  const menu = picker.querySelector(".schedule-date-menu");
  const previous = picker.querySelector("[data-date-previous]");
  const next = picker.querySelector("[data-date-next]");
  const months = [
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
  ];
  const shortMonths = [
    "ม.ค.",
    "ก.พ.",
    "มี.ค.",
    "เม.ย.",
    "พ.ค.",
    "มิ.ย.",
    "ก.ค.",
    "ส.ค.",
    "ก.ย.",
    "ต.ค.",
    "พ.ย.",
    "ธ.ค.",
  ];
  const weekdays = ["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"];
  const pad = (number) => String(number).padStart(2, "0");
  const toIso = (date) =>
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
  const toDate = (iso) => {
    const [year, month, day] = iso.split("-").map(Number);
    return new Date(year, month - 1, day);
  };
  const params = new URLSearchParams(window.location.search);
const urlDate = params.get("date");

let selectedDate = urlDate ? toDate(urlDate) : new Date();

let viewDate = new Date(
  selectedDate.getFullYear(),
  selectedDate.getMonth(),
  1,
);

  const updateTrigger = () => {
    triggerText.textContent = `${selectedDate.getDate()} ${shortMonths[selectedDate.getMonth()]} ${selectedDate.getFullYear() + 543}`;
  };
  const closeMenu = () => {
    menu.hidden = true;
    trigger.setAttribute("aria-expanded", "false");
  };
  const selectDate = (date) => {
    selectedDate = new Date(
      date.getFullYear(),
      date.getMonth(),
      date.getDate(),
    );
    viewDate = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1);
    source.value = toIso(selectedDate);
    source.dispatchEvent(new Event("change", { bubbles: true }));
    updateTrigger();
    closeMenu();
    trigger.focus();
  };
  const renderCalendar = () => {
    menu.replaceChildren();
    const header = document.createElement("div");
    header.className = "schedule-calendar-header";
    const title = document.createElement("p");
    title.className = "schedule-calendar-title";
    title.textContent = `${months[viewDate.getMonth()]} ${viewDate.getFullYear() + 543}`;
    const navigation = document.createElement("div");
    navigation.className = "schedule-calendar-nav";
    [
      ["‹", -1, "เดือนก่อนหน้า"],
      ["›", 1, "เดือนถัดไป"],
    ].forEach(([icon, direction, label]) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = icon;
      button.setAttribute("aria-label", label);
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        viewDate = new Date(
          viewDate.getFullYear(),
          viewDate.getMonth() + direction,
          1,
        );
        renderCalendar();
      });
      navigation.append(button);
    });
    header.append(title, navigation);
    const grid = document.createElement("div");
    grid.className = "schedule-date-grid";
    weekdays.forEach((weekdayName) => {
      const weekday = document.createElement("span");
      weekday.className = "schedule-date-weekday";
      weekday.textContent = weekdayName;
      grid.append(weekday);
    });
    const firstDay = viewDate.getDay();
    const daysInMonth = new Date(
      viewDate.getFullYear(),
      viewDate.getMonth() + 1,
      0,
    ).getDate();
    const todayIso = toIso(new Date());
    const selectedIso = toIso(selectedDate);
    for (let index = 0; index < firstDay; index += 1)
      grid.append(document.createElement("span"));
    for (let day = 1; day <= daysInMonth; day += 1) {
      const date = new Date(viewDate.getFullYear(), viewDate.getMonth(), day);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "schedule-date-day";
      button.textContent = String(day);
      button.setAttribute(
        "aria-label",
        `${day} ${months[date.getMonth()]} ${date.getFullYear() + 543}`,
      );
      if (toIso(date) === todayIso) button.classList.add("is-today");
      if (toIso(date) === selectedIso) button.classList.add("is-selected");
      button.addEventListener("click", () => selectDate(date));
      grid.append(button);
    }
    menu.append(header, grid);
  };

  source.value = toIso(selectedDate);
  updateTrigger();
  trigger.addEventListener("click", () => {
    const isClosed = menu.hidden;
    if (isClosed) renderCalendar();
    menu.hidden = !isClosed;
    trigger.setAttribute("aria-expanded", String(isClosed));
  });
  previous.addEventListener("click", () =>
    selectDate(
      new Date(
        selectedDate.getFullYear(),
        selectedDate.getMonth(),
        selectedDate.getDate() - 1,
      ),
    ),
  );
  next.addEventListener("click", () =>
    selectDate(
      new Date(
        selectedDate.getFullYear(),
        selectedDate.getMonth(),
        selectedDate.getDate() + 1,
      ),
    ),
  );
  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-schedule-date-picker]")) closeMenu();
  });
});
