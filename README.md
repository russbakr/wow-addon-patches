# WoW Addon Patches

Personal patches to third-party WoW addons that fix taint-related error spam in retail.
Kept here so they survive CurseForge updates and can be shared / reapplied easily.

## Patches

### 1. BlizzMove — `SetScale` retaint guard
**Addon:** https://www.curseforge.com/wow/addons/blizzmove
**Status:** Upstreamed as **[Kiatra/BlizzMove#182](https://github.com/Kiatra/BlizzMove/pull/182)**.
**What it fixes:**
- `Blizzard_UIWidgetTemplateTextWithState.lua:35: attempt to perform arithmetic on local 'textHeight' (a secret number value tainted by 'BlizzMove')` — ~14,000/session on affected characters
- `Blizzard_SharedXML/LayoutFrame.lua:491: attempt to compare a secret number value (tainted by 'BlizzMove')`

**How:** Guard `frame:SetScale(newScale)` in `SetFrameScale` so it only fires when the scale is actually changing. The addon was calling `SetScale` on every `OnShow`, re-tainting the value each time, even when restoring an already-correct scale. See the PR body for the full write-up.

Patch file: [`patches/BlizzMove.lua.patch`](patches/BlizzMove.lua.patch)

### 2. TooltipPlus — unguarded `:GetUnit()` calls
**Addon:** https://www.curseforge.com/wow/addons/tooltipplus
**Status:** No public git repo exists. Posted in the CurseForge comments; applied locally.
**What it fixes:**
- `Blizzard_SharedXMLGame/Tooltip/TooltipUtil.lua:39: bad argument #1 to '?' (Usage: local unitName, unitServer = UnitName(unit). Secret values are only allowed during untainted execution for this argument.)` — **14,747 hits in a single session** on an affected character (the single biggest source of error spam observed).

**How:** `GameTooltip:GetUnit()` internally calls `UnitName(unit)`, which throws when the tooltip is being rendered via `SetWorldCursor` with a tainted unit token. The author already `pcall`-wrapped every downstream call (`UnitExists`, `UnitIsPlayer`, `UnitClass`, etc.) but missed three spots where `:GetUnit()` itself is called bare. We wrap those in `pcall` too, with a fallback to `"mouseover"` where appropriate.

Patch files:
- [`patches/TooltipPlus-General.lua.patch`](patches/TooltipPlus-General.lua.patch)
- [`patches/TooltipPlus-Core.lua.patch`](patches/TooltipPlus-Core.lua.patch)

## Applying the patches

### On a fresh install or after a CurseForge update

```powershell
# From the folder containing this repo:
.\apply-patches.ps1
```

The script finds your retail WoW install, applies each patch to the relevant addon file, and reports what changed. Safe to re-run — it detects if a patch is already applied and skips.

### Manually

Each `.patch` file is a standard unified diff. Apply with `git apply` from inside the corresponding addon folder:
```powershell
cd "C:\Program Files (x86)\World of Warcraft\_retail_\Interface\AddOns\BlizzMove"
git apply "<path-to-this-repo>\patches\BlizzMove.lua.patch"
```

## After a patched addon is updated upstream

Once BlizzMove merges #182, you can stop applying its patch — just delete `patches/BlizzMove.lua.patch` and the matching block in `apply-patches.ps1`. Same for TooltipPlus if its author ever publishes a fix.

## License

Patches are offered under the same license as the upstream addon they patch.
