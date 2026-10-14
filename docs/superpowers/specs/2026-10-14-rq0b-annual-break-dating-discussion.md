# Discussion log: Plan 1b spec (RQ0b annual break dating)

Notes from the owner's review of `2026-10-14-rq0b-annual-break-dating-design.md`, kept so the discussion can resume where it left off. Decisions are recorded in the spec itself (§8) once made.

## 2026-10-14

**Status:** spec review paused so the remaining Plan 1 review item (counties split across metro lines) can be handled first. No spec changes made yet.

**Q (owner): The metro break search can only name break years from about 1977. Can that be brought down to 1969?**

Answer (spec partner):
- 1977 isn't where the data starts; it's the earliest year the test may *name* as the break. The standard rule leaves the first and last 15% of years (about 8 of 55) off the candidate list so each side has enough data. The 1969–76 data still counts as "before" data.
- If the true break were earlier (say 1972), the test would still detect a change but place it at the edge (1977), so an edge estimate reads "1977 or earlier".
- Ways to reach the early 1970s:
  1. The 1929+ state series already covers them (the spec's main tool for early dates).
  2. Trim less for metros: 10% → earliest candidate about 1975; 5% → about 1972. Cost: estimates near the edge rest on 3–5 "before" years, the bar for calling a break rises roughly 10%, and the year range widens. 5% is about the lowest in common use.
  3. Adding Plan 1's 1940–60 decade data to the metro series: not recommended (mixes ten-year and one-year data; 1940 metro income is wages only).
- **Recommendation:** keep 15% for the main metro result; add a 5% version as a check; write "at or before" when the estimate lands on the edge; rely on the 1929+ state series for early-1970s dating. If approved, the spec partner edits §4.2–4.3 and §7.

**Owner decision:** pending.

**Also noted:** §9 still says the Plan 1 review is "in progress"; the review fixes are committed (D-26), so the precondition for decision 1 (order of work) is met. To be updated when the spec is next edited.

## Open decisions (spec §8)
1. Order of work: Plan 1b before Plan 2 (RQ0a), on a new branch.
2. Energy-state rule: objective (1980 mining share ≥ 3× national) vs. hand-picked list.
3. Where results go: new section in notebook 1.1 vs. a separate notebook.
4. (From the discussion above) metro trimming: 15% main + 5% check.
