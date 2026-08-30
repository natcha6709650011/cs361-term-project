const API_BASE_URL =
  "https://aisw93f81a.execute-api.us-east-1.amazonaws.com/v1";

document.addEventListener("DOMContentLoaded", loadRoomDetail);

async function loadRoomDetail() {
  const loading = document.querySelector("#room-loading");
  const errorBox = document.querySelector("#room-error");
  const roomPage = document.querySelector("#room-page");

  try {
    if (loading) loading.style.display = "none";
    if (errorBox) errorBox.style.display = "none";
    if (roomPage) roomPage.style.display = "none";

    const params = new URLSearchParams(window.location.search);
    const roomNumber = params.get("room");

    if (!roomNumber) {
      throw new Error("ไม่พบเลขห้องใน URL");
    }

    const response = await fetch(
      `${API_BASE_URL}/rooms/${encodeURIComponent(roomNumber)}`,
      {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }

    let room = await response.json();

    console.log("API Room Detail:", room);

    if (room?.data) {
      room = room.data;
    }

    if (room?.room) {
      room = room.room;
    }

    displayRoomDetail(room);

    if (roomPage) roomPage.style.display = "block";
  } catch (error) {
    console.error("Error loading room detail:", error);

    if (loading) loading.style.display = "none";
    if (roomPage) roomPage.style.display = "none";
    if (errorBox) errorBox.style.display = "none";
  }
}


// ==============================
// helper
// ==============================

function getRoomNumber(room) {
  return String(
    room?.room_number ??
    room?.roomNumber ??
    room?.number ??
    room?.room_no ??
    ""
  );
}


function getRoomType(room) {
  if (typeof room?.room_type === "string") {
    return room.room_type;
  }

  if (room?.room_type?.type_name) {
    return room.room_type.type_name;
  }

  if (room?.room_type_name) {
    return room.room_type_name;
  }

  if (room?.type_name) {
    return room.type_name;
  }

  return "ห้อง";
}


function getAmenities(room) {
  let value =
    room?.amenities ??
    room?.amenities_json ??
    [];

  if (typeof value === "string") {
    try {
      value = JSON.parse(value);
    } catch {
      value = [];
    }
  }

  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => {
      if (typeof item === "string") {
        return item;
      }

      return (
        item?.item ??
        item?.name ??
        item?.label ??
        item?.amenity_name ??
        ""
      );
    })
    .filter(Boolean);
}


function getRoles(room) {
  let value =
    room?.allowed_roles ??
    room?.allowed_roles_json ??
    [];

  if (typeof value === "string") {
    try {
      value = JSON.parse(value);
    } catch {
      value = [];
    }
  }

  if (!Array.isArray(value)) {
    return [];
  }

  const roleNames = {
    teacher: "อาจารย์",
    staff: "บุคลากร",
    student: "นักศึกษา",
    undergrad: "นักศึกษาปริญญาตรี",
    grad: "นักศึกษาปริญญาโท",
    phd: "นักศึกษาปริญญาเอก",
  };

  return value.map((role) => {
    if (typeof role === "string") {
      return roleNames[role] || role;
    }

    return (
      role?.name ??
      role?.label ??
      role?.role_name ??
      ""
    );
  }).filter(Boolean);
}


function getDescription(room) {
  return (
    room?.description ??
    room?.description_th ??
    room?.room_description ??
    room?.detail ??
    room?.details ??
    ""
  );
}


function getBuilding(room) {
  return (
    room?.building ??
    room?.building_name ??
    room?.buildingName ??
    ""
  );
}


function getRoomSize(room) {
  return (
    room?.room_size ??
    room?.roomSize ??
    room?.size ??
    room?.size_m ??
    ""
  );
}


// ==============================
// display
// ==============================

function displayRoomDetail(room) {

  console.log("ข้อมูลที่จะนำมาแสดง:", room);

  const number = getRoomNumber(room);

  const displayName = number
    ? `บร2-${number}`
    : "ไม่ระบุห้อง";

  const type = getRoomType(room);

  const floor =
    room?.floor ??
    room?.floor_number ??
    room?.floorNumber ??
    null;

  const capacity =
    room?.capacity ??
    room?.seat_capacity ??
    room?.seats ??
    null;

  const building = getBuilding(room);

  const roomSize = getRoomSize(room);

  const description = getDescription(room);

  const amenities = getAmenities(room);

  const roles = getRoles(room);

  // =========================
  // ชื่อห้อง
  // =========================

  const roomName = document.querySelector("#room-name");

  if (roomName) {
    roomName.textContent = displayName;
  }


  // =========================
  // breadcrumb
  // =========================

  const breadcrumb = document.querySelector("#room-breadcrumb");

  if (breadcrumb) {
    breadcrumb.textContent = displayName;
  }


  // =========================
  // ประเภทห้อง
  // =========================

  const roomType = document.querySelector("#room-type");

  if (roomType) {
    roomType.textContent = type;
  }


  // =========================
  // ตำแหน่ง
  // =========================

  const roomLocation = document.querySelector("#room-location");

  if (roomLocation) {

    if (floor !== null && floor !== "") {
      roomLocation.textContent =
        `ห้อง ${number} ชั้น ${floor}`;
    } else {
      roomLocation.textContent =
        `ห้อง ${number}`;
    }
  }


  // =========================
  // ความจุ
  // =========================

  const capacityElement =
    document.querySelector("#room-capacity");

  if (capacityElement) {

    capacityElement.textContent =
      capacity !== null && capacity !== ""
        ? `${capacity} ที่นั่ง`
        : "ไม่ระบุ";
  }


  // =========================
  // ชั้น
  // =========================

  const floorElement =
    document.querySelector("#room-floor");

  if (floorElement) {

    floorElement.textContent =
      floor !== null && floor !== ""
        ? `ชั้น ${floor}`
        : "ไม่ระบุ";
  }





  // =========================
  // ขนาดห้อง
  // =========================

  const sizeElement =
    document.querySelector("#room-size");

  if (sizeElement) {

    sizeElement.textContent =
      roomSize || "ไม่ระบุ";
  }


  // =========================
  // รายละเอียดห้อง
  // =========================

  const descriptionElement =
    document.querySelector("#room-description");

  if (descriptionElement) {

    descriptionElement.textContent =
      description || "ไม่มีรายละเอียดห้อง";
  }


  // =========================
  // รูปภาพ
  // =========================

  const roomImage =
    document.querySelector("#room-image");

  if (roomImage) {

    const imageUrl =
      room?.image_url ??
      room?.imageUrl ??
      room?.photo_url ??
      room?.photoUrl ??
      "";

    if (imageUrl) {
      roomImage.src = imageUrl;
      roomImage.alt = `ห้อง ${displayName}`;
    }
  }


  // =========================
  // อุปกรณ์
  // =========================

  const amenitiesContainer =
    document.querySelector("#room-amenities");

  if (amenitiesContainer) {

    amenitiesContainer.replaceChildren();

    if (amenities.length === 0) {

      const span = document.createElement("span");
      span.textContent = "ไม่มีข้อมูล";
      amenitiesContainer.appendChild(span);

    } else {

      amenities.forEach((amenity) => {

        const span =
          document.createElement("span");

        span.textContent = amenity;

        amenitiesContainer.appendChild(span);
      });
    }
  }


  // =========================
  // สิทธิ์การใช้งาน
  // =========================

  const rolesContainer =
    document.querySelector("#room-roles");

  if (rolesContainer) {

    rolesContainer.replaceChildren();

    if (roles.length === 0) {

      const span = document.createElement("span");

      span.textContent = "ไม่มีข้อมูล";

      rolesContainer.appendChild(span);

    } else {

      roles.forEach((role) => {

        const span =
          document.createElement("span");

        span.textContent = role;

        rolesContainer.appendChild(span);
      });
    }
  }


  // =========================
  // title browser
  // =========================

  document.title =
    `${displayName} | CS Thammasat`;
}