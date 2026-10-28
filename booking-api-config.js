// Booking API configuration. Keep token handling in one place so every
// booking action is authenticated as the currently signed-in user.
(function configureBookingApi() {
  const remoteBaseUrl = "https://7i1mw8hw5l.execute-api.us-east-1.amazonaws.com";

  window.BOOKING_API_CONFIG = {
    mode: "api",
    // The local dev proxy avoids browser CORS during local testing.
    baseUrl: window.location.port === "5501" ? "/api" : remoteBaseUrl,
    // Authentication now relies on the HttpOnly session_token cookie sent via
    // credentials: 'include'. No JWT is read from localStorage.
    useCredentials: true,
  };
})();
