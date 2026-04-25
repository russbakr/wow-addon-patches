# WoW Addon Patches

Personal patches to third-party WoW addons that fix taint-related error spam in retail.
Kept here so they survive CurseForge updates and can be shared / reapplied easily.

## Patches

### TooltipPlus — unguarded `:GetUnit()` calls
**Addon:** https://www.curseforge.com/wow/addons/tooltipplus
**Status:** No public git repo exists. Posted in the CurseForge comments; applied locally.
**What it fixes:**
- `Blizzard_SharedXMLGame/Tooltip/TooltipUtil.lua:39: bad argument #1 to '?' (Usage: local unitName, unitServer = UnitName(unit). Secret values are only allowed during untainted execution for this argument.)` — **14,747 hits in a single session** on an affected character (the single biggest source of error spam observed).

**How:** `GameTooltip:GetUnit()` internally calls `UnitName(unit)`, which throws when the tooltip is being rendered via `SetWorldCursor` with a tainted unit token. The author already `pcall`-wrapped every downstream call (`UnitExists`, `UnitIsPlayer`, `UnitClass`, etc.) but missed three spots where `:GetUnit()` itself is called bare. We wrap those in `pcall` too, with a fallback to `"mouseover"` where appropriate.

Patch files:
- [`patches/TooltipPlus-General.lua.patch`](patches/TooltipPlus-General.lua.patch)
- [`patches/TooltipPlus-Core.lua.patch`](patches/TooltipPlus-Core.lua.patch)

## Failed attempts (kept for the lesson)

### BlizzMove — `SetScale` retaint guard ❌ *theory was wrong*

Originally I theorised that `BlizzMove`'s `SetScale` calls were tainting the frame scale value, which then propagated into Blizzard's widget layout math when hovering map POIs. Submitted as [Kiatra/BlizzMove#182](https://github.com/Kiatra/BlizzMove/pull/182), which was **closed by Numynum (collaborator)** with this correction:

> *"taint does not propagate through scale values, they cannot be tainted"*

So that whole approach was misguided. Whatever produces the BlizzMove-attributed taint errors in BugSack comes from a different mechanism — not from `SetScale`. The patch and PR are kept linked above as documentation of the (failed) attempt; do not apply.

## Applying the patches

### On a fresh install or after a CurseForge update

```powershell
powershell -ExecutionPolicy Bypass -File .\apply-patches.ps1
```

The script finds your retail WoW install, applies each patch to the relevant addon file, and reports what changed. Safe to re-run — it detects if a patch is already applied and skips.

### Manually

Each `.patch` file is a standard unified diff. Apply with `git apply` from inside the AddOns folder:
```powershell
cd "C:\Program Files (x86)\World of Warcraft\_retail_\Interface\AddOns"
git apply "<path-to-this-repo>\patches\TooltipPlus-General.lua.patch"
git apply "<path-to-this-repo>\patches\TooltipPlus-Core.lua.patch"
```

## After a patched addon is updated upstream

If TooltipPlus's author ever publishes a fix, just delete the `patches/TooltipPlus-*.patch` files and stop running `apply-patches.ps1`.

## License

Patches are offered under the same license as the upstream addon they patch.
