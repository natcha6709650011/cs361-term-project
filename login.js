const loginForm = document.getElementById('loginForm');
const loginError = document.getElementById('loginError');
const API_BASE_URL = window.location.port === '5501'
    ? '/api/v1'
    : 'https://7i1mw8hw5l.execute-api.us-east-1.amazonaws.com/v1';
const LOGIN_API_URL = `${API_BASE_URL}/auth/login`;

loginForm.addEventListener('submit', async function (event) {

    event.preventDefault();

    const username =
        document.getElementById('username').value.trim();

    const password =
        document.getElementById('password').value;

    // à¸•à¸£à¸§à¸ˆà¸ªà¸­à¸šà¸‚à¹‰à¸­à¸¡à¸¹à¸¥
    if (!username || !password) {

        loginError.textContent =
            'à¸à¸£à¸¸à¸“à¸²à¸à¸£à¸­à¸ username à¹à¸¥à¸° password';

        loginError.style.display = 'block';

        return;
    }

    // à¸‹à¹ˆà¸­à¸™ error à¹€à¸”à¸´à¸¡
    loginError.style.display = 'none';

    try {

        const response = await fetch(
            LOGIN_API_URL,
            {
                method: 'POST',

                credentials: 'include',

                headers: {
                    'Content-Type': 'application/json'
                },

                body: JSON.stringify({
                    username: username,
                    password: password
                })
            }
        );

        const data = await response.json();

        // Login à¹„à¸¡à¹ˆà¸ªà¸³à¹€à¸£à¹‡à¸ˆ
        if (!response.ok || !data.status) {

            loginError.textContent =
                data.message ||
                'Username à¸«à¸£à¸·à¸­ Password à¹„à¸¡à¹ˆà¸–à¸¹à¸à¸•à¹‰à¸­à¸‡';

            loginError.style.display = 'block';

            return;
        }

        // ==========================================
        // Login à¸ªà¸³à¹€à¸£à¹‡à¸ˆ
        // ==========================================

        const user = data.user || {};


        // à¸‚à¹‰à¸­à¸¡à¸¹à¸¥ User
        localStorage.setItem(
            'tuUser',
            JSON.stringify(user)
        );

        // Username
        localStorage.setItem(
            'username',
            user.username || username
        );

        // à¸ªà¸–à¸²à¸™à¸° Login
        localStorage.setItem(
            'isLoggedIn',
            'true'
        );

        // ==========================================
        // Debug
        // ==========================================

        // ==========================================
        // à¹„à¸›à¸«à¸™à¹‰à¸²à¹à¸£à¸
        // ==========================================

        window.location.href = 'index.html';

    } catch (error) {

        console.error(
            'Login error:',
            error
        );

        loginError.textContent =
            'à¹„à¸¡à¹ˆà¸ªà¸²à¸¡à¸²à¸£à¸–à¹€à¸Šà¸·à¹ˆà¸­à¸¡à¸•à¹ˆà¸­à¸£à¸°à¸šà¸š Login à¹„à¸”à¹‰';

        loginError.style.display = 'block';
    }


});
