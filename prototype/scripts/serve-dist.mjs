import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize, sep } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../dist/", import.meta.url));
const types = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
};

function sendText(response, status, body) {
  response.writeHead(status, { "content-type": "text/plain; charset=utf-8" });
  response.end(body);
}

createServer(async (request, response) => {
  let pathname;
  try {
    pathname = decodeURIComponent(new URL(request.url ?? "/", "http://127.0.0.1").pathname);
  } catch {
    sendText(response, 400, "Bad request");
    return;
  }
  if (pathname === "/") pathname = "/index.html";
  let filePath = normalize(join(root, pathname));
  if (!filePath.startsWith(root.endsWith(sep) ? root : `${root}${sep}`)) {
    sendText(response, 400, "Bad request");
    return;
  }
  try {
    let data;
    try {
      data = await readFile(filePath);
    } catch {
      data = await readFile(join(root, "index.html"));
      filePath = "index.html";
    }
    response.writeHead(200, { "content-type": types[extname(filePath)] || "application/octet-stream" });
    response.end(data);
  } catch (error) {
    // Details stay in this local terminal; the browser only gets a generic message.
    console.error("prototype preview failed:", error);
    sendText(response, 500, "Internal server error");
  }
}).listen(5173, "127.0.0.1", () => {
  console.log("Lá Lành prototype preview: http://127.0.0.1:5173/");
});
