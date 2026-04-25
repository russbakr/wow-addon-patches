# WoW Addon Patches

Personal patches to third-party WoW addons that fix taint-related error spam in retail.
Kept here so they survive CurseForge updates and can be shared / reapplied easily.

## TL;DR — if you see "tainted by 'BlizzMove'" errors, the culprit is probably TooltipPlus

If your BugSack is full of:
- `tainted by 'BlizzMove'` widget layout errors (`Blizzard_UIWidgetTemplateTextWithState.lua:35` arithmetic on `textHeight`, `LayoutFrame.lua:491` comparison failures), AND
- `Blizzard_SharedXMLGame/Tooltip/TooltipUtil.lua:39` `bad argument #1 to '?'` errors (often *much* more numerous — 14k+/session in our case),

…BlizzMove is almost certainly **not** the cause. Per Kiatra/BlizzMove maintainer Numynum, scale values cannot be tainted, and BlizzMove's own taint log is clean. The leading theory: another addon taints something in the shared tooltip pipeline, the error system misattributes it to BlizzMove. Patching TooltipPlus's three unguarded `:GetUnit()` calls eliminated **both** error families simultaneously in our test — even with BlizzMove untouched. See [Kiatra/BlizzMove#182](https://github.com/Kiatra/BlizzMove/pull/182) for the full discussion.

The Blizzard-side bug that lets these secret values leak into widget layout in the first place is reportedly fixed in WoW patch **12.0.5**, so this whole error family should self-resolve once that lands. Until then, the TooltipPlus patches below kill the spam.

## Patches

### TooltipPlus — unguarded `:GetUnit()` calls
**Addon:** https://www.curseforge.com/wow/addons/tooltipplus
**Status:** No public git repo exists. Posted in the CurseForge comments; applied locally.
**What it fixes:**
- `Blizzard_SharedXMLGame/Tooltip/TooltipUtil.lua:39: bad argument #1 to '?' (Usage: local unitName, unitServer = UnitName(unit). Secret values are only allowed during untainted execution for this argument.)` — **14,747 hits in a single session** on an affected character (the single biggest source of error spam observed).
- *Likely also fixes the `tainted by 'BlizzMove'` widget layout errors via the misattribution mechanism above.* In our testing, both error families disappeared together after patching TooltipPlus alone.

**How:** `GameTooltip:GetUnit()` internally calls `UnitName(unit)`, which throws when the tooltip is being rendered via `SetWorldCursor` with a tainted unit token. The author already `pcall`-wrapped every downstream call (`UnitExists`, `UnitIsPlayer`, `UnitClass`, etc.) but missed three spots where `:GetUnit()` itself is called bare. We wrap those in `pcall` too, with a fallback to `"mouseover"` where appropriate.

Patch files:
- [`patches/TooltipPlus-General.lua.patch`](patches/TooltipPlus-General.lua.patch)
- [`patches/TooltipPlus-Core.lua.patch`](patches/TooltipPlus-Core.lua.patch)

## Failed attempts (kept for the lesson)

### BlizzMove — `SetScale` retaint guard ❌ *theory was wrong*

Originally I theorised that `BlizzMove`'s `SetScale` calls were tainting the frame scale value, which then propagated into Blizzard's widget layout math when hovering map POIs. Submitted as [Kiatra/BlizzMove#182](https://github.com/Kiatra/BlizzMove/pull/182), which was **closed by Numynum (collaborator)** with this correction:

> *"taint does not propagate through scale values, they cannot be tainted"*

In a follow-up comment Numynum added the missing context:
- The "secret value" half of the error comes from a known **Blizzard bug** where secrets linger in tooltip data longer than they should — being fixed in **patch 12.0.5**, hence the `cant-fix` label on issue #181 (waiting on Blizzard).
- BlizzMove getting *blamed* in the error attribution is most likely **misattribution** caused by another addon's interaction with the shared tooltip / widget pipeline. *"I've not seen this error occur with just BlizzMove loaded, no matter how hard I tried."*

This explains why patching TooltipPlus alone made the BlizzMove-attributed errors disappear too: the actual taint was coming from TooltipPlus, BlizzMove was just an innocent name in the stack trace. Lesson: don't assume the addon named in the taint error is the addon causing the taint.

The patch and PR are kept linked above as documentation of the (failed) attempt; do not apply.

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
