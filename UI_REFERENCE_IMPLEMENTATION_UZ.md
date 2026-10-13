# AVTOPARK PRO — reference UI implementation

## What changed
- Warehouse view gets a reference-inspired banner with warehouse photography, tighter five-column KPI cards, compact tabs/table and responsive layout.
- App shell gets a truck/road visual footer in the dark sidebar.
- Super Admin `Platform` screen gets an elite dark-purple command-center visual treatment while retaining the existing API calls.
- Driver role gets a separate mobile-first home page with trip summary, fuel receipt link, issue-report link, chat shortcut and bottom navigation.
- Page-level lazy loading remains enabled.

## Images
- Warehouse: `https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=1600&q=85`
- Truck: `https://images.unsplash.com/photo-1519003722824-194d4455a60c?auto=format&fit=crop&w=900&q=85`
- Driver map background: `https://images.unsplash.com/photo-1524666041070-9e8762b2f9c4?auto=format&fit=crop&w=1400&q=85`

These URLs require network access in the browser. For a fully self-contained deployment, download licensed images into `frontend/public/images/` and reference them locally.

## Validation notes
- Changes are integrated in the existing React app rather than being a disconnected mockup.
- Existing API-backed Warehouse and Platform workflows are retained; driver quick actions navigate to existing modules.
- No live browser visual regression test or successful production build is claimed. Package installation from npm registry was unavailable in the build environment (`EAI_AGAIN`), so Recharts was not added as an imported dependency in this archive. Existing Warehouse overview keeps its current data-driven visual summaries. If Recharts is required, install it in the project environment with `npm install recharts` and replace/extend the chart panels after dependency installation.
- CSS layer is standalone and does not require Tailwind. Existing project currently does not configure Tailwind; these classes are implemented using the project's CSS architecture to avoid introducing an uninstalled build plugin.
