# TooltipPlus — CurseForge comment template

**Post on:** https://www.curseforge.com/wow/addons/tooltipplus (comments section)

---

Hi @Gorby — great addon, using it daily. Found a bug that spams BugSack on every mouseover: **14,000+ errors in a single play session**.

**Error:**
```
Blizzard_SharedXMLGame/Tooltip/TooltipUtil.lua:39:
  bad argument #1 to '?' (Usage: local unitName, unitServer = UnitName(unit).
  Secret values are only allowed during untainted execution for this argument.)
```

**Root cause:** `GameTooltip:GetUnit()` internally calls `UnitName(unit)`, which errors when the tooltip is being rendered via `SetWorldCursor` (world mouseover) with a tainted unit token. You've correctly `pcall`-wrapped downstream calls (`UnitExists`, `UnitIsPlayer`, `UnitClass`, `UnitReaction`, etc.) but the `:GetUnit()` call itself is unprotected in three places:

- `General.lua:14` — `GetTooltipUnit()` — fires on every mouseover via `OnShow`, the biggest offender
- `Core.lua:435` — `isUnit` branch of the `ProcessInfo` hook
- `Core.lua:548` — `UpdateUnitDisplay()`

Two other callsites (`Core.lua:114` and `Core.lua:335`) are already properly wrapped.

**Fix:** wrap each of the three unprotected `:GetUnit()` calls in `pcall`, with a fallback to the `"mouseover"` unit token where appropriate. Applied locally and the error count dropped from ~14,700 per session to ~0.

If it's helpful I can describe the exact diffs in more detail, or if you publish the source on GitHub I'd be happy to send a PR.

Thanks for the addon!

---

## (Alternative) If you can find Gorby's GitHub

If there turns out to be a source repo anywhere (not listed in the .toc), the same patch can go as a PR. The three edits are trivial — each one turns `select(2, frame:GetUnit())` into `pcall(frame.GetUnit, frame)` plus an `ok` check.
