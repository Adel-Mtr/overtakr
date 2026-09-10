# Hosted portfolio demo handoff

`render-demo.yaml` is an optional two-service Render Blueprint for the existing Next.js and FastAPI application. It has not been applied or validated against a connected Render account. The existing root `render.yaml` is unchanged.

## Launch order

1. Connect the intended Render workspace and inspect its existing services and spending limits before creating resources.
2. Create the backend and frontend services from this repository using the Blueprint as the specification. Confirm the actual assigned public HTTPS URLs; do not guess them from service names.
3. Set `CORS_ALLOW_ORIGINS` and `FRONTEND_URL` on the backend to the frontend origin.
4. Set `NEXT_PUBLIC_API_BASE_URL` on the frontend to the backend origin, then build/deploy the frontend. This value is embedded at build time.
5. Verify backend health, season/race/driver loading, a complete strategy analysis and scenario sharing in a browser.
6. Capture the actual application screenshots described below, then add the verified demo URL and screenshots to the main README and GitHub profile.

The two resources request the free compute plan and disable automatic redeployment. This is not a guarantee of zero account charges: check workspace usage and spend limits before launch. Free services share an instance-hour allowance, spin down when idle and lose local cache files on restart. FastF1 cold-load memory and latency must be tested on the chosen instance before calling the demo portfolio-ready. Do not silently upgrade to a paid plan.

References: [Render Blueprint fields](https://render.com/docs/blueprint-spec), [free service limits](https://render.com/docs/free).

## Screenshot acceptance criteria

- Desktop: select an available completed race, run analysis successfully, and show Strategy Delta Charts with the leaderboard.
- Mobile: capture the strategy builder at a narrow viewport with readable controls and no horizontal clipping.
- Use real rendered UI. Do not manufacture prediction results, performance metrics or a hosted-demo screenshot.
- Exclude admin interfaces, credentials, personal uploads and browser account chrome.
- Store approved images under `docs/screenshots/`, with a caption identifying the race and any demo data used.

## Repository presentation

Suggested description: **F1 race-strategy comparison and analysis with Next.js, TypeScript and FastAPI.**

Suggested topics: `nextjs`, `react`, `typescript`, `fastapi`, `python`, `docker`, `formula-1`.

Pin Overtakr first on the profile. Set the repository website field only after the deployed URL has passed the checks above.
