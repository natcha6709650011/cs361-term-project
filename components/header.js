// ======================================================
// CSTU Room Booking - Header Role-Based Menu
// ======================================================

document.addEventListener("DOMContentLoaded", () => {
    updateHeaderMenu();
    setupMenuToggle();
    setupDropdown();
});


// ------------------------------------------------------
// Get current user
// ------------------------------------------------------

function getHeaderUser() {
    const storedUser = localStorage.getItem("tuUser");

    if (!storedUser) {
        return null;
    }

    try {
        return JSON.parse(storedUser);
    } catch (error) {
        console.error("Invalid tuUser:", error);
        return null;
    }
}


// ------------------------------------------------------
// Update menu according to role
// ------------------------------------------------------

function updateHeaderMenu() {

    const user = getHeaderUser();

    const loginLink = document.querySelector('[data-menu="login"]');
    const logoutLink = document.querySelector('[data-menu="logout"]');
    const bookingLink = document.querySelector('[data-menu="booking"]');
    const myBookingLink = document.querySelector('[data-menu="my-bookings"]');
    const approveLink = document.querySelector('[data-menu="approve"]');
    const manageRoomLink = document.querySelector('[data-menu="manage-room"]');
    const profileLink = document.querySelector('[data-menu="profile"]');

    // ------------------------------------------
    // ยังไม่ได้ Login
    // ------------------------------------------

    if (!user) {

        if (loginLink) {
            loginLink.style.display = "";
        }

        if (logoutLink) {
            logoutLink.style.display = "none";
        }

        if (bookingLink) {
            bookingLink.style.display = "none";
        }

        if (myBookingLink) {
            myBookingLink.style.display = "none";
        }

        if (approveLink) {
            approveLink.style.display = "none";
        }

        if (manageRoomLink) {
            manageRoomLink.style.display = "none";
        }

        if (profileLink) {
            profileLink.style.display = "none";
        }

        return;
    }


    // ------------------------------------------
    // Login แล้ว
    // ------------------------------------------

    if (loginLink) {
        loginLink.style.display = "none";
    }

    if (logoutLink) {
        logoutLink.style.display = "";
    }

    if (bookingLink) {
        bookingLink.style.display = "";
    }

    if (myBookingLink) {
        myBookingLink.style.display = "";
    }

    if (profileLink) {
        profileLink.style.display = "";
    }


    // ------------------------------------------
    // Approver
    // ------------------------------------------

    if (approveLink) {

        if (user.role === "approver") {
            approveLink.style.display = "";
        } else {
            approveLink.style.display = "none";
        }
    }


    // ------------------------------------------
    // Facility Admin
    // ------------------------------------------

    if (manageRoomLink) {

        if (user.role === "facility_admin") {
            manageRoomLink.style.display = "";
        } else {
            manageRoomLink.style.display = "none";
        }
    }
}


// ------------------------------------------------------
// Mobile menu
// ------------------------------------------------------

function setupMenuToggle() {

    const menuButton = document.querySelector(".menu-toggle");
    const navigation = document.querySelector(".main-nav");

    if (!menuButton || !navigation) {
        return;
    }

    menuButton.addEventListener("click", () => {

        const isOpen = navigation.classList.toggle("open");

        menuButton.setAttribute(
            "aria-expanded",
            String(isOpen)
        );

        menuButton.setAttribute(
            "aria-label",
            isOpen ? "ปิดเมนู" : "เปิดเมนู"
        );
    });
}


// ------------------------------------------------------
// Dropdown menu
// ------------------------------------------------------

function setupDropdown() {

    const dropdown = document.querySelector(".nav-dropdown");
    const dropdownButton = document.querySelector(".dropdown-toggle");

    if (!dropdown || !dropdownButton) {
        return;
    }

    dropdownButton.addEventListener("click", () => {

        const isOpen = dropdown.classList.toggle("open");

        dropdownButton.setAttribute(
            "aria-expanded",
            String(isOpen)
        );
    });


    document.addEventListener("click", (event) => {

        if (!dropdown.contains(event.target)) {

            dropdown.classList.remove("open");

            dropdownButton.setAttribute(
                "aria-expanded",
                "false"
            );
        }
    });
}


// ------------------------------------------------------
// Logout
// ------------------------------------------------------



async function logoutUser() {
    const AUTH_API_URL =
        "https://7i1mw8hw5l.execute-api.us-east-1.amazonaws.com/v1/auth/logout";

    try {
        const response = await fetch(AUTH_API_URL, {
            method: "POST",
            credentials: "include"
        });

        if (!response.ok) {
            console.error(
                "Logout API failed:",
                response.status,
                await response.text()
            );
        } else {
            console.log("Logout API succeeded:", response.status);
        }
    } catch (error) {
        console.error("Logout network error:", error);
    } finally {
        localStorage.removeItem("tuUser");
        localStorage.removeItem("authToken");
        localStorage.removeItem("username");
        localStorage.removeItem("isLoggedIn");

        window.location.href = "login.html";
    }
}
