# Vitalog automation

Vitalog can keep itself up to date with a **morning routine**: a scheduled Claude session that runs once a day, pulls what it can, writes it into the dashboard, writes a short morning brief, and e-mails the brief to you.

| Source | Automatic? | How |
|---|---|---|
| **Oura** | Yes | One-time 30-day login token (steps below). The routine pulls the last 14 days of sleep, readiness, activity, HRV, resting heart rate, SpO₂ and steps. Renew the token once a month. |
| **Hume, MyFitnessPal (iPhone)** | Yes, via Apple Health | An iPhone Shortcut e-mails yesterday's Health numbers to your own Gmail each morning; the routine reads that mail. |
| **myAir** | No | ResMed has no export and its login needs e-mail verification codes. Tap *Log last night* in the app (ten seconds). |
| **Morning brief** | Yes | The routine writes today's guidance into the Guide tab and e-mails it to you. |

The routine writes into the dashboard's private storage on claude.ai (documents `vitalog/feed` and `vitalog/config`). Vitalog must be opened through its claude.ai link for the synced data to show; the GitHub Pages copy shows only what is on that device.

## 1. Publish the site (once)

GitHub → repo Settings → Pages → Source: **GitHub Actions**, then merge this branch. Your site is `https://<username>.github.io/<repo>/`. The Oura login needs the page `https://<username>.github.io/<repo>/oauth.html` to exist.

## 2. Connect Oura (once, then once a month)

1. Sign in at <https://cloud.ouraring.com/oauth/applications> and create an application. Name: anything. Redirect URI: your `oauth.html` address, exactly.
2. In Vitalog (claude.ai link) → Sources → Oura → **Connect Oura**. Paste the Client ID and the redirect address, tap **Open Oura login**, approve.
3. Oura sends you to `oauth.html`, which shows a token. Copy it, go back to Vitalog, paste it in the same sheet, **Save token**.

The token lasts 30 days. Vitalog shows the expiry on the Oura card; repeat step 2 and 3 when it runs out.

## 3. Apple Health by e-mail (iPhone, optional)

Turn on Apple Health syncing inside Hume and MyFitnessPal first. Then build one Shortcut:

1. Shortcuts app → Automation → **+** → Time of Day, 06:30, Daily, *Run Immediately*.
2. Actions, in order (each `Find Health Samples` sorted by *Start Date*, latest first, limit 1 unless noted):
   - `Find Health Samples` Weight → `Get Details of Health Sample` Value → `Text`: `Weight: [Value] kg`
   - `Find Health Samples` Body Fat Percentage → Value → `Text`: `Body Fat: [Value]`
   - `Find Health Samples` Steps, *Start Date is yesterday*, no limit → `Calculate Statistics` Sum → `Text`: `Steps: [Result]`
   - `Find Health Samples` Sleep, *Start Date is yesterday*, no limit → `Calculate Statistics` Sum of Duration → `Text`: `Sleep: [Result] min`
   - `Find Health Samples` Dietary Energy, *Start Date is yesterday* → Sum → `Text`: `Calories: [Result]`
   - Same for Protein, Carbohydrates, Total Fat, Dietary Water.
   - `Combine Text` (new lines), then `Send Email` to yourself, subject **Vitalog Health**, *Show Compose Sheet* off.

Any line of the form `Name: number unit` works. Add a `Date: 2026-09-10` line to date the values; without it the routine uses yesterday. Apps like *Health Auto Export* can send the same e-mail if you prefer not to build the Shortcut.

## 4. Turn on the morning routine

The routine already exists in your Claude Routines list as **Vitalog morning sync**, paused. Once Oura is connected (or the Health e-mail is arriving), tell Claude "turn on my Vitalog morning sync" or enable it from the Routines page. It runs daily at 12:00 UTC by default; ask Claude to move it to your morning.

What it does each run, in order: read `vitalog/config` and `vitalog/state` from the dashboard, run `health-app/automation/sync.py` for Oura, read Gmail for the latest **Vitalog Health** mail, merge everything into `vitalog/feed`, write a morning brief into the feed, and e-mail the brief to you (turn e-mail off by asking Claude to set `emailBrief` to false).

## Privacy

The Oura token is a read-only, 30-day key stored in the dashboard's private storage, which only you can open unless you share the page. Revoke it any time at <https://cloud.ouraring.com/account/apps>. Health e-mails stay in your Gmail; the routine only reads ones with the subject **Vitalog Health**.
