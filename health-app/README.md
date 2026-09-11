# Vitalog

A personal health logbook that runs on your phone as an installable web app. Nothing is uploaded anywhere: every entry is stored in the phone's browser storage, and you can export a backup as a JSON file at any time.

## What it does

- **Today** – water meter with a one-tap +glass button, latest weight / blood pressure / heart rate / sleep / mood tiles, today's medication checklist, quick log buttons, and today's entries.
- **Trends** – 7 / 30 / 90 day charts for weight, blood pressure, heart rate, glucose, sleep, mood, pain, water, exercise and temperature. Drag a finger across a chart to read values. Every chart has a table view.
- **History** – every entry grouped by day, filterable by type, with delete.
- **Meds** – medications with a dose, one or more daily times and notes. Doses show up on Today as a checklist and a 7-day adherence figure is shown here.
- **Settings** (gear icon) – units (kg/lb, mg/dL/mmol/L, °C/°F), water goal, reminder notifications, install instructions, export / import backup, clear example data, delete everything.

The app starts with **example data** so you can see how it works. Tap "Clear it" on the banner to start with your own.

## Your other apps (Sources tab)

None of these apps offer a public API a web page can call without a server, so Vitalog imports the export each one already provides and merges everything into one daily record, tagged by source:

| App | How the data gets in | What comes through |
|---|---|---|
| **Oura** | Oura on the Web → Trends → *Download Data* (CSV), or Membership Hub → *Export data* (ZIP/JSON) | Sleep, readiness and activity scores, HRV, resting heart rate, sleep time, breathing rate, temperature deviation, SpO₂, steps |
| **MyFitnessPal** | myfitnesspal.com → Settings → Privacy & Security → *Download your data* (free, ZIP by email), or Premium *Export data* | Calories, protein, carbs, fat, fiber, sugar, sodium, exercise, weight |
| **Hume** | Syncs to Apple Health; import the Apple Health export. Or tap *Log body composition* | Weight, body fat, muscle mass, visceral fat |
| **Apple Health** | Health app → profile → *Export All Health Data* → import `export.zip` | Everything above from any app that syncs to Health, each tagged with its source |
| **myAir (ResMed)** | No export exists. Tap *Log last night* and type the score, hours, AHI and leak | myAir score, usage, AHI, mask leak |

Manual entries always win over imported values for the same day. Each import shows which columns were read and which were ignored.

## Guidance from Claude (Guide tab)

When Vitalog is opened through its claude.ai artifact link, the Guide tab can ask Claude for **Today's guidance** (last night plus the past week) or a **Weekly review** (this week against the last four). Claude sees only the numbers in the app plus the "About me" note in Settings. Guidance is saved in the app. Outside claude.ai the tab offers a *Copy my summary* button to paste into any Claude chat.

Opened through claude.ai, the data is also mirrored to the artifact's private storage so a phone and a computer share one logbook (imports are easier on a computer).

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
