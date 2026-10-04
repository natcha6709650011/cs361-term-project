document.querySelectorAll("[data-date-picker]").forEach((picker) => {
  const source = picker.querySelector(".date-source");
  const trigger = picker.querySelector(".date-trigger");
  const triggerText = trigger.querySelector("span");
  const menu = picker.querySelector(".date-menu");
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
  const weekdays = ["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"];
  let viewDate = new Date();
  viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth(), 1);
  const pad = (number) => String(number).padStart(2, "0");
  const toIso = (date) =>
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;

  const closeMenu = () => {
    menu.hidden = true;
    trigger.setAttribute("aria-expanded", "false");
  };

  const selectDate = (date) => {
    source.value = toIso(date);
    source.dispatchEvent(new Event("change", { bubbles: true }));
    triggerText.textContent = `${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()}`;
    trigger.classList.remove("is-placeholder");
    closeMenu();
    trigger.focus();
  };

  const renderCalendar = () => {
    menu.replaceChildren();

    const header = document.createElement("div");
    header.className = "date-menu__header";

    const title = document.createElement("p");
    title.className = "date-menu__title";
    title.textContent = `${months[viewDate.getMonth()]} ${viewDate.getFullYear() + 543}`;

    const nav = document.createElement("div");
    nav.className = "date-menu__nav";

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

      nav.append(button);
    });

    header.append(title, nav);

    const grid = document.createElement("div");
    grid.className = "date-grid";

    weekdays.forEach((day) => {
      const weekday = document.createElement("span");
      weekday.className = "date-weekday";
      weekday.textContent = day;
      grid.append(weekday);
    });

    const firstDay = viewDate.getDay();

    const daysInMonth = new Date(
      viewDate.getFullYear(),
      viewDate.getMonth() + 1,
      0,
    ).getDate();

    const selectedIso = source.value;
    const todayIso = toIso(new Date());

    for (let index = 0; index < firstDay; index += 1) {
      grid.append(document.createElement("span"));
    }

    for (let day = 1; day <= daysInMonth; day += 1) {
      const date = new Date(
        viewDate.getFullYear(),
        viewDate.getMonth(),
        day,
      );

      const button = document.createElement("button");
      button.type = "button";
      button.className = "date-day";
      button.textContent = String(day);

      button.setAttribute(
        "aria-label",
        `${day} ${months[date.getMonth()]} ${date.getFullYear() + 543}`,
      );

      if (toIso(date) === todayIso) {
        button.classList.add("is-today");
      }

      if (toIso(date) === selectedIso) {
        button.classList.add("is-selected");
      }

      button.addEventListener("click", () => selectDate(date));
      grid.append(button);
    }

    menu.append(header, grid);
  };

  source.value = "";

  trigger.addEventListener("click", () => {
    const isClosed = menu.hidden;

    if (isClosed) {
      renderCalendar();
    }

    menu.hidden = !isClosed;
    trigger.setAttribute("aria-expanded", String(isClosed));
  });
});



document.querySelectorAll("[data-time-picker]").forEach((picker) => {
  const source = picker.querySelector(".time-source");
  const trigger = picker.querySelector(".time-trigger");
  const triggerText = trigger.querySelector("span");
  const menu = picker.querySelector(".time-menu");

  source.querySelectorAll("option").forEach((option) => {
    if (option.disabled) return;

    const choice = document.createElement("button");
    choice.type = "button";
    choice.className = "time-option";
    choice.role = "option";
    choice.dataset.value = option.value;
    choice.textContent = option.textContent;
    choice.setAttribute("aria-selected", String(option.selected));

    choice.addEventListener("click", () => {
      source.value = option.value;
      source.dispatchEvent(new Event("change", { bubbles: true }));

      triggerText.textContent = option.textContent;
      trigger.classList.remove("is-placeholder");

      menu
        .querySelectorAll(".time-option")
        .forEach((item) =>
          item.setAttribute("aria-selected", "false"),
        );

      choice.setAttribute("aria-selected", "true");
      closeMenu();
      trigger.focus();
    });

    menu.append(choice);
  });

  function closeMenu() {
    menu.hidden = true;
    trigger.setAttribute("aria-expanded", "false");
  }

  function openMenu() {
    document.querySelectorAll("[data-time-picker]").forEach((otherPicker) => {
      if (otherPicker !== picker) {
        otherPicker.querySelector(".time-menu").hidden = true;
        otherPicker
          .querySelector(".time-trigger")
          .setAttribute("aria-expanded", "false");
      }
    });

    menu.hidden = false;
    trigger.setAttribute("aria-expanded", "true");
  }

  trigger.addEventListener("click", () =>
    menu.hidden ? openMenu() : closeMenu(),
  );

  trigger.addEventListener("keydown", (event) => {
    if (["ArrowDown", "Enter", " "].includes(event.key)) {
      event.preventDefault();
      openMenu();

      (
        menu.querySelector('[aria-selected="true"]') ||
        menu.querySelector(".time-option")
      )?.focus();
    }

    if (event.key === "Escape") {
      closeMenu();
    }
  });

  source.addEventListener("change", () => {
    triggerText.textContent =
      source.options[source.selectedIndex].textContent;

    trigger.classList.toggle("is-placeholder", !source.value);
  });
});



document.querySelectorAll("[data-capacity-picker]").forEach((picker) => {
  const source = picker.querySelector(".capacity-source");
  const trigger = picker.querySelector(".capacity-trigger");
  const triggerText = trigger.querySelector("span");
  const menu = picker.querySelector(".capacity-menu");
  const customInput = picker.querySelector(".capacity-custom-input");

  const closeMenu = () => {
    menu.hidden = true;
    trigger.setAttribute("aria-expanded", "false");
  };

  const showCustomInput = () => {
    closeMenu();

    picker.classList.add("is-custom");
    trigger.hidden = true;
    customInput.hidden = false;

    source.value = "";
    source.dispatchEvent(new Event("change", { bubbles: true }));

    customInput.focus();
  };

  const showTrigger = () => {
    picker.classList.remove("is-custom");
    trigger.hidden = false;
    customInput.hidden = true;
  };

  source.querySelectorAll("option").forEach((option) => {
    if (option.disabled) return;

    const choice = document.createElement("button");
    choice.type = "button";
    choice.className = "capacity-option";
    choice.role = "option";
    choice.textContent = option.textContent;
    choice.dataset.value = option.value;
    choice.setAttribute("aria-selected", "false");

    choice.addEventListener("click", () => {
      if (option.value === "custom") {
        showCustomInput();
        return;
      }

      showTrigger();

      source.value = option.value;
      source.dispatchEvent(new Event("change", { bubbles: true }));

      triggerText.textContent = option.textContent;
      trigger.classList.remove("is-placeholder");

      menu
        .querySelectorAll(".capacity-option")
        .forEach((item) =>
          item.setAttribute("aria-selected", "false"),
        );

      choice.setAttribute("aria-selected", "true");

      closeMenu();
      trigger.focus();
    });

    menu.append(choice);
  });

  trigger.addEventListener("click", () => {
    const isClosed = menu.hidden;

    document
      .querySelectorAll(".capacity-menu")
      .forEach((otherMenu) => (otherMenu.hidden = true));

    document
      .querySelectorAll(".capacity-trigger")
      .forEach((otherTrigger) =>
        otherTrigger.setAttribute("aria-expanded", "false"),
      );

    menu.hidden = !isClosed;
    trigger.setAttribute("aria-expanded", String(isClosed));
  });

    customInput.addEventListener("input", () => {
    const value = customInput.value;

    let customOption = source.querySelector("[data-custom-value]");

    if (!customOption) {
      customOption = document.createElement("option");
      customOption.dataset.customValue = "true";
      source.append(customOption);
    }

    customOption.value = value;
    customOption.textContent = value ? `${value} คน` : "";

    source.value = value;
    source.dispatchEvent(new Event("change", { bubbles: true }));
  });

  // คลิกช่องกรอกอีกครั้ง = กลับไปเลือกความจุแบบเดิม
  customInput.addEventListener("click", () => {
    const value = customInput.value;

    if (value) {
      triggerText.textContent = `${value} คน`;
      trigger.classList.remove("is-placeholder");
    } else {
      triggerText.textContent = "เลือกความจุ";
      trigger.classList.add("is-placeholder");
    }

    showTrigger();

    menu.hidden = false;
    trigger.setAttribute("aria-expanded", "true");
  });
});
document.querySelectorAll("[data-room-type-picker]").forEach((picker) => {
  const source = picker.querySelector(".room-type-source");
  const trigger = picker.querySelector(".room-type-trigger");
  const triggerText = trigger.querySelector("span");
  const menu = picker.querySelector(".room-type-menu");

  const closeMenu = () => {
    menu.hidden = true;
    trigger.setAttribute("aria-expanded", "false");
  };

  source.querySelectorAll("option").forEach((option) => {
    const choice = document.createElement("button");

    choice.type = "button";
    choice.className = "room-type-option";
    choice.role = "option";
    choice.textContent = option.textContent;
    choice.setAttribute("aria-selected", String(option.selected));

    choice.addEventListener("click", () => {
      source.value = option.value;
      source.dispatchEvent(new Event("change", { bubbles: true }));

      triggerText.textContent = option.textContent;

      menu
        .querySelectorAll(".room-type-option")
        .forEach((item) =>
          item.setAttribute("aria-selected", "false"),
        );

      choice.setAttribute("aria-selected", "true");

      closeMenu();
      trigger.focus();
    });

    menu.append(choice);
  });

  trigger.addEventListener("click", () => {
    const isClosed = menu.hidden;

    document
      .querySelectorAll(".room-type-menu")
      .forEach((otherMenu) => (otherMenu.hidden = true));

    document
      .querySelectorAll(".room-type-trigger")
      .forEach((otherTrigger) =>
        otherTrigger.setAttribute("aria-expanded", "false"),
      );

    menu.hidden = !isClosed;
    trigger.setAttribute("aria-expanded", String(isClosed));
  });
});



document.addEventListener("click", (event) => {
  if (
    !event.target.closest(
      "[data-date-picker], [data-time-picker], [data-capacity-picker], [data-room-type-picker]",
    )
  ) {
    document.querySelectorAll("[data-date-picker]").forEach((picker) => {
      picker.querySelector(".date-menu").hidden = true;
      picker
        .querySelector(".date-trigger")
        .setAttribute("aria-expanded", "false");
    });

    document.querySelectorAll("[data-time-picker]").forEach((picker) => {
      picker.querySelector(".time-menu").hidden = true;
      picker
        .querySelector(".time-trigger")
        .setAttribute("aria-expanded", "false");
    });

    document.querySelectorAll("[data-capacity-picker]").forEach((picker) => {
      picker.querySelector(".capacity-menu").hidden = true;
      picker
        .querySelector(".capacity-trigger")
        .setAttribute("aria-expanded", "false");
    });

    document.querySelectorAll("[data-room-type-picker]").forEach((picker) => {
      picker.querySelector(".room-type-menu").hidden = true;
      picker
        .querySelector(".room-type-trigger")
        .setAttribute("aria-expanded", "false");
    });
  }
});



document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    document.querySelectorAll("[data-date-picker]").forEach((picker) => {
      picker.querySelector(".date-menu").hidden = true;
      picker
        .querySelector(".date-trigger")
        .setAttribute("aria-expanded", "false");
    });

    document.querySelectorAll("[data-time-picker]").forEach((picker) => {
      picker.querySelector(".time-menu").hidden = true;
      picker
        .querySelector(".time-trigger")
        .setAttribute("aria-expanded", "false");
    });

    document.querySelectorAll("[data-capacity-picker]").forEach((picker) => {
      picker.querySelector(".capacity-menu").hidden = true;
      picker
        .querySelector(".capacity-trigger")
        .setAttribute("aria-expanded", "false");
    });

    document.querySelectorAll("[data-room-type-picker]").forEach((picker) => {
      picker.querySelector(".room-type-menu").hidden = true;
      picker
        .querySelector(".room-type-trigger")
        .setAttribute("aria-expanded", "false");
    });
  }
});