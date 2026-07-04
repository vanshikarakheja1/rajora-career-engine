import { writeFileSync } from "node:fs";

const apiBaseUrl = (process.env.CAREER_ENGINE_API_URL || "").replace(/\/$/, "");

writeFileSync(
  "frontend/config.js",
  `window.CAREER_ENGINE_CONFIG = ${JSON.stringify({ apiBaseUrl }, null, 2)};\n`,
  "utf8",
);

console.log(`Frontend API base URL: ${apiBaseUrl || "(same origin)"}`);
