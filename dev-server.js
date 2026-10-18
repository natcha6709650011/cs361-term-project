// Local development server for this project.
// It serves the website and forwards /api/* to the AWS API Gateway so the
// browser does not need to make a cross-origin request during local testing.
const http = require("http");
const https = require("https");
const fs = require("fs");
const path = require("path");

const PORT = 5501;
const PROJECT_ROOT = __dirname;
const API_HOST = "7i1mw8hw5l.execute-api.us-east-1.amazonaws.com";
const MIME_TYPES = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
};

function proxyToApi(request, response) {
  const upstreamPath = request.url.replace(/^\/api/, "") || "/";
  const headers = { ...request.headers, host: API_HOST };
  delete headers.origin;

  const upstreamRequest = https.request(
    { hostname: API_HOST, path: upstreamPath, method: request.method, headers },
    (upstreamResponse) => {
      response.writeHead(upstreamResponse.statusCode || 502, upstreamResponse.headers);
      upstreamResponse.pipe(response);
    },
  );

  upstreamRequest.on("error", (error) => {
    console.error("API proxy error:", error.message);
    if (!response.headersSent) {
      response.writeHead(502, { "Content-Type": "application/json; charset=utf-8" });
    }
    response.end(JSON.stringify({ message: "ไม่สามารถเชื่อมต่อ API ได้" }));
  });
  request.pipe(upstreamRequest);
}

function serveFile(request, response) {
  const requestPath = decodeURIComponent(request.url.split("?")[0]);
  const fileName = requestPath === "/" ? "/index.html" : requestPath;
  const filePath = path.resolve(PROJECT_ROOT, `.${fileName}`);

  if (!filePath.startsWith(`${PROJECT_ROOT}${path.sep}`)) {
    response.writeHead(403).end("Forbidden");
    return;
  }

  fs.readFile(filePath, (error, file) => {
    if (error) {
      response.writeHead(error.code === "ENOENT" ? 404 : 500).end("Not found");
      return;
    }
    response.writeHead(200, {
      "Content-Type": MIME_TYPES[path.extname(filePath).toLowerCase()] || "application/octet-stream",
      "Cache-Control": "no-store",
    });
    response.end(file);
  });
}

http.createServer((request, response) => {
  if (request.url.startsWith("/api/")) {
    proxyToApi(request, response);
    return;
  }
  serveFile(request, response);
}).listen(PORT, "127.0.0.1", () => {
  console.log(`Local server: http://127.0.0.1:${PORT}/login.html`);
});
