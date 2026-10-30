/*
 * Keeps the capacities on the home-page recommendation cards aligned with
 * the room inventory. Room numbers live in the markup; capacities do not.
 */
(function loadHomeRoomCapacities() {
  const API_URL = window.location.port === "5501"
    ? "/api/v1/rooms"
    : "/api/rooms"; // Amplify rewrite: /api/<*> -> API Gateway /v1/<*>
  const capacityElements = [...document.querySelectorAll("[data-room-capacity]")];

  function getRooms(payload) {
    if (Array.isArray(payload)) return payload;
    return payload?.data ?? payload?.rooms ?? payload?.items ?? [];
  }

  function roomNumber(room) {
    return String(room?.room_number ?? room?.roomNumber ?? room?.number ?? "");
  }

  function roomCapacity(room) {
    const value = room?.capacity ?? room?.seat_capacity ?? room?.seats;
    const number = Number(value);
    return Number.isFinite(number) && number >= 0 ? number : null;
  }

  function setCapacity(element, value) {
    const icon = element.querySelector("svg");
    element.replaceChildren();
    if (icon) element.append(icon);
    element.append(document.createTextNode(value === null ? "ไม่ระบุความจุ" : `${value} ที่นั่ง`));
  }

  async function load() {
    if (!capacityElements.length) return;

    try {
      const response = await fetch(API_URL, { headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error(`Unable to load rooms: ${response.status}`);

      const rooms = getRooms(await response.json());
      const roomsByNumber = new Map(rooms.map((room) => [roomNumber(room), room]));

      capacityElements.forEach((element) => {
        setCapacity(element, roomCapacity(roomsByNumber.get(element.dataset.roomCapacity)));
      });
    } catch (error) {
      console.error("Unable to load home-room capacities:", error);
      capacityElements.forEach((element) => setCapacity(element, null));
    }
  }

  load();
})();
