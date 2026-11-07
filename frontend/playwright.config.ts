import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  use: { baseURL: "http://127.0.0.1:3000" },
  webServer: [
    {
      command: "SEEKORA_DEMO_MODE=true SEEKORA_RATE_LIMIT_ENABLED=false SEEKORA_ADMIN_API_KEY=seekora-e2e-key SEEKORA_CORS_ORIGINS=http://127.0.0.1:3000 ../.venv/bin/uvicorn app.main:app --app-dir ../backend --host 127.0.0.1 --port 8000",
      url: "http://127.0.0.1:8000/v1/health",
      reuseExistingServer: false,
    },
    {
      command: "NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run dev -- --hostname 127.0.0.1",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: false,
    },
  ],
});
