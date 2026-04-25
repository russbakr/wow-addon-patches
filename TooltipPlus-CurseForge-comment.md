# TooltipPlus — CurseForge comment template

**Post on:** https://www.curseforge.com/wow/addons/tooltipplus (comments section)

---

Hi @Gorby — great addon, using it daily. Found a bug that spams BugSack on every mouseover: **14,000+ errors in a single play session**.

*(Note: the diagnosis below was assisted by an AI tool; the patches were tested against my live install and verified to drop the error count to ~0.)*

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

Two other callsites (`Core.lua:114` and `Core.lua:335`) are already properly wrapped — so the pattern is already in place, just missed in three spots.

**Fix:** wrap each unprotected `:GetUnit()` call in `pcall`, with a fallback to the `"mouseover"` unit token where appropriate. Applied locally and the error count dropped from ~14,700 per session to ~0.

**Bonus finding (might be worth knowing):** these errors also leak into Blizzard's tooltip widget layout code, where they show up in BugSack as `tainted by 'BlizzMove'` errors (`Blizzard_UIWidgetTemplateTextWithState.lua:35` arithmetic on `textHeight`, etc.) — even though BlizzMove isn't the cause. Confirmed in conversation with the BlizzMove maintainer (Numynum) on [Kiatra/BlizzMove#182](https://github.com/Kiatra/BlizzMove/pull/182): leading theory is shared-library / tooltip-pipeline taint that the error system misattributes. Patching just the three TooltipPlus callsites above made **both** the TooltipPlus and BlizzMove-attributed errors disappear together. So this fix likely helps quite a few users who currently think BlizzMove is the culprit.

If it's helpful I can describe the exact diffs in more detail, or if you publish the source on GitHub I'd be happy to send a PR.

Thanks for the addon!

---

## Diffs reference (in case you want them inline)

```lua
-- General.lua, GetTooltipUnit() — replace:
local unitName, unitId = GameTooltip:GetUnit()
-- with:
local ok, unitName, unitId = pcall(GameTooltip.GetUnit, GameTooltip)
if not ok then
    local okMo, existsMo = pcall(UnitExists, "mouseover")
    if okMo and existsMo then return "mouseover" end
    return nil
end
```

```lua
-- Core.lua, line 435 (in isUnit branch of ProcessInfo hook) — replace:
local unit = select(2, self:GetUnit())
if unit then
-- with:
local okUnit, _, unit = pcall(self.GetUnit, self)
if okUnit and unit then
```

```lua
-- Core.lua, line 548 (UpdateUnitDisplay) — replace:
local unit = tip.GetUnit and select(2, tip:GetUnit())
-- with:
local unit
if tip.GetUnit then
    local okUnit, _, resUnit = pcall(tip.GetUnit, tip)
    if okUnit then unit = resUnit end
end
```
