document.addEventListener("DOMContentLoaded", async () => {
    const approverTab = document.getElementById("approver-tab");

    if (!approverTab) return;

    const token = localStorage.getItem("authToken");

    // ยังไม่ได้ login → ซ่อน
    if (!token) {
        approverTab.hidden = true;
        return;
    }

    try {
        const response = await fetch(
            "https://7i1mw8hw5l.execute-api.us-east-1.amazonaws.com/v1/me/permissions",
            {
                method: "GET",
                headers: {
                    "Accept": "application/json",
                    "Authorization": `Bearer ${token}`
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