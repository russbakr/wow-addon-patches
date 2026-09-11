# Vitalog

A personal health logbook that runs on your phone as an installable web app. Nothing is uploaded anywhere: every entry is stored in the phone's browser storage, and you can export a backup as a JSON file at any time.

## What it does

- **Today** – water meter with a one-tap +glass button, latest weight / blood pressure / heart rate / sleep / mood tiles, today's medication checklist, quick log buttons, and today's entries.
- **Trends** – 7 / 30 / 90 day charts for weight, blood pressure, heart rate, glucose, sleep, mood, pain, water, exercise and temperature. Drag a finger across a chart to read values. Every chart has a table view.
- **History** – every entry grouped by day, filterable by type, with delete.
- **Meds** – medications with a dose, one or more daily times and notes. Doses show up on Today as a checklist and a 7-day adherence figure is shown here.
- **Settings** (gear icon) – units (kg/lb, mg/dL/mmol/L, °C/°F), water goal, reminder notifications, install instructions, export / import backup, clear example data, delete everything.

The app starts with **example data** so you can see how it works. Tap "Clear it" on the banner to start with your own.

## Put it on your phone

The app needs to be served over HTTPS to be installable and to work offline. The included GitHub Actions workflow publishes this folder to GitHub Pages.

1. In the GitHub repo, open **Settings → Pages** and set **Source** to **GitHub Actions**.
2. Merge this branch into `main` (or run the "Publish Vitalog to GitHub Pages" workflow manually from the Actions tab).
3. Open `https://<your-username>.github.io/<repo-name>/` on your phone.
4. **Android (Chrome):** menu → *Add to Home screen* / *Install app*. **iPhone (Safari):** Share → *Add to Home Screen*.

After that it opens full screen like any other app, works offline, and keeps the data on that phone.

## Reminders

Web apps cannot schedule notifications the way native apps can. Vitalog checks every 30 seconds while it is open (or in the background on Android after installing) and fires a notification within 30 minutes of a scheduled dose time that has not been ticked off. The Today checklist always shows what is due regardless.

## Backups

Settings → **Export backup** shares a `vitalog-backup-<date>.json` file (to Drive, iCloud, email, whatever you pick). **Import a backup** restores it on any phone. Do this occasionally: clearing the browser's site data wipes the app's storage.

## Files

| File | Purpose |
|---|---|
| `index.html` | The whole app: styles, markup and code in one file |
| `manifest.webmanifest` | Name, icons and colours used when installing to the home screen |
| `sw.js` | Service worker that caches the app so it opens offline |
| `icons/` | App icons (generated, no external assets) |

Vitalog is a logbook, not medical advice. Blood pressure categories follow the American Heart Association guide.
