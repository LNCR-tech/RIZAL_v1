# RIZAL_v1

The frontend now lives under [`frontend/`](frontend). Root-level app files were moved there so the repo is easier to scan and the GitHub Pages workflow can build from one place.

Current layout:

- [`frontend/`](frontend): Aura Vue app, Docker files, Pages build, Capacitor Android workspace
- [`Back-End/`](Back-End): backend-related assets already in the repo
- [`event-attendance/`](event-attendance): event attendance module
- [`1.Technical Documentation/`](<1.Technical Documentation>): project documentation
- `VALID8_DOCKER COPY/` and `VALID8_DOCKER_FINAL/`: legacy snapshots kept as-is

Frontend commands:

```powershell
cd frontend
npm install
npm run dev
npm run build
```

GitHub Pages now builds `frontend/dist` instead of uploading the whole repository.
