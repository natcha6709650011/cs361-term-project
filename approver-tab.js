document.addEventListener("DOMContentLoaded", async () => {
    const approverTab = document.getElementById("approver-tab");

    if (!approverTab) return;

    const loggedIn = localStorage.getItem("isLoggedIn") === "true";

    // ยังไม่ได้ login → ซ่อน
    if (!loggedIn) {
        approverTab.hidden = true;
        return;
    }

    try {
        // Local (dev-server.js): /api/v1/<*> | Amplify rewrite: /api/<*> -> API Gateway /v1/<*>
        const apiBaseUrl = window.location.port === "5501" ? "/api/v1" : "/api";

        const response = await fetch(
            `${apiBaseUrl}/me/permissions`,
            {
                method: "GET",
                credentials: "include",
                headers: {
                    "Accept": "application/json"
                }
            }
        );

        if (!response.ok) {
            approverTab.hidden = true;
            return;
        }

        const data = await response.json();

        // แสดงเฉพาะผู้ที่เป็น Approver
        if (data.user?.is_approver === true) {
            approverTab.hidden = false;
        } else {
            approverTab.hidden = true;
        }

    } catch (error) {
        console.error("Unable to load user permissions:", error);
        approverTab.hidden = true;
    }
});