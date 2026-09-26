import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize } from "node:path";

const root = new URL("../dist/", import.meta.url);
const types = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
};

createServer(async (request, response) => {
  try {
    const url = new URL(request.url, "http://127.0.0.1");
    let pathname = decodeURIComponent(url.pathname);
    if (pathname === "/") pathname = "/index.html";
    let filePath = normalize(join(root.pathname, pathname));
    if (!filePath.startsWith(root.pathname)) throw new Error("Bad path");
    let data;
    try {
      data = await readFile(filePath);
    } catch {
      data = await readFile(new URL("index.html", root));
      filePath = "index.html";
    }
    response.writeHead(200, { "content-type": types[extname(filePath)] || "application/octet-stream" });
    response.end(data);
  } catch (error) {
    response.writeHead(500, { "content-type": "text/plain; charset=utf-8" });
    response.end(String(error));
  }
}).listen(5173, "127.0.0.1", () => {
  console.log("Lá Lành prototype preview: http://127.0.0.1:5173/");
});
