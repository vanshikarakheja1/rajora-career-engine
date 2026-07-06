import { writeFileSync } from "node:fs";

const useSameOriginApi = process.env.VERCEL && process.env.CAREER_ENGINE_USE_DIRECT_API !== "true";
const apiBaseUrl = useSameOriginApi ? "" : (process.env.CAREER_ENGINE_API_URL || "").replace(/\/$/, "");

writeFileSync(
  "frontend/config.js",
  `window.CAREER_ENGINE_CONFIG = ${JSON.stringify({ apiBaseUrl }, null, 2)};\n`,
  "utf8",
);

console.log(`Frontend API base URL: ${apiBaseUrl || "(same origin)"}`);
