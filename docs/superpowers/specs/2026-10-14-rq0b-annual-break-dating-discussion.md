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

**Owner decision:** accepted (15% main + 5% check), 2026-10-14.

**Also noted:** §9 still says the Plan 1 review is "in progress"; the review fixes are committed (D-26), so the precondition for decision 1 (order of work) is met. To be updated when the spec is next edited.

## Open decisions (spec §8)
1. Order of work: Plan 1b before Plan 2 (RQ0a), on a new branch.
2. Energy-state rule: objective (1980 mining share ≥ 3× national) vs. hand-picked list.
3. Where results go: new section in notebook 1.1 vs. a separate notebook.
4. (From the discussion above) metro trimming: 15% main + 5% check.

## Note for the spec (from the Plan 1 review, 2026-10-14)
- County splits across metro lines are now flagged in the metro panel (`growth_comparable`, D-27). The annual metro panel in Plan 1b should drop the affected unit-years the same way (the split year itself: Broomfield 2001, La Paz 1983, Cibola 1981; Los Alamos 1949 and Menominee 1961 fall before 1969). To be added to spec §3 when it is next edited.

## Spec partner's final handoff (2026-10-14; agent closed, discussion folded back into the main session)

No spec edits were made. Owner decisions still pending on everything below.

### Recommendations on the open decisions
1. **Order of work (§8.1):** Plan 1b before Plan 2 (RQ0a), on a new branch off `plan-1-rq0b`. Nothing blocks it (D-26, D-27 done), and it creates `us_metro_annual`, which build step 5 extends.
2. **Energy-state rule (§8.2):** the objective rule (1980 mining share of earnings ≥ 3× national), with the resulting list shown to the owner before any results are run. If it misses an obvious oil state, use the hand-picked list (TX, OK, LA, WY, AK, NM, WV, ND) as a robustness check.
3. **Where results go (§8.3):** a new section in notebook 1.1 plus one paragraph in the RQ0b results.
4. **Metro trimming (new):** 15% main + 5% check (earliest metro candidate about 1972; Andrews 5% critical value for one restriction is about 8.85 at 15% trimming vs. about 9.8 at 5%); write "at or before" when an estimate is at the edge; use the 1929+ state series (candidates about 1943–2009) for early-1970s dating.

### Issues found in the spec, not yet raised with the owner
- **a. Two scales for β (§4.2, §5).** The pooled model uses one-year growth, so β_before and β_after are roughly 1/10 of the ten-year β. Show them ×10 as well, and name the columns `beta_before_annual` and `beta_after_annual` (or add a `horizon` column).
- **b. Trusting the break-year range (§4.2, §6).** A unit-resampling bootstrap isn't guaranteed to have correct coverage for a break date. Check it by simulation: across ≥ 200 synthetic panels, the 90% range should contain the planted year 80–97% of the time. Report Bai's (1997) interval alongside.
- **c. Multi-break cross-check speed (§4.2).** Brute force over up to 3 breaks is about 100,000 fits for states (about 4,800 rows × about 100 year dummies) and about 14,000 for metros. Demean within year once, and/or use the Bai-Perron (2003) dynamic-programming search.
- **d. WWII (§4.3, §7).** Annual state population in 1940–46 swings with troops and war industry. Add a robustness check that excludes growth years 1940–1946, and a matching risks row.
- **e. Population-sum test before 1950 (§6).** Exclude Alaska and Hawaii before 1950 (BEA zeros, dropped per D-24); otherwise the 1930/1940 1% check passes only by luck (together about 0.4% of the US).
- **f. Results table (§5).** Add a `trim` column once decision 4 is accepted.
- **g. Stale status (§9).** Step 2a should read "Done (Plan 1); review fixes committed (D-26, D-27)".
- **h. No change needed:** annual growth ends 2023→2024 (state income runs to 2025, but population is only needed to 2024).

### Edits to make once the owner decides
- **Any edit:** fix §9 step 2a (item g).
- **D-27, already decided:** in §3, unit-years whose growth crosses a county split are dropped (Broomfield 2001, La Paz 1983, Cibola 1981); in §6, a data test that those metro-years are absent.
- **Decision 4, if accepted:**
  - §4.2: the 5% check and the "at or before" reading;
  - §4.3: a 5% trimming row;
  - §7: the last risks row;
  - §5: the `trim` column;
  - §8: the decision and its date.
- **Decisions 1–3:** mark each in §8 with the choice and date. If the hand-picked energy list is chosen, update the §4.3 row and the §6 synthetic test wording; if a separate notebook is chosen, update the §5 notebook row and the §9 paper note.
- **Items a–f:** only if the owner approves them.

### Data facts (`data/interim/bea.parquet`)
- County personal income and population: 1969–2024.
- State income per person: 1929–2025.
- State population: not downloaded yet (SAINC1 line 2, the one new request the spec lists).

## Owner decisions (2026-10-14, main session)
- Decisions 1–4: all accepted as recommended. Recorded in spec §8.
- Edits made: §3 (D-27 drops), §4.2 (5% check, "at or before"), §4.3 (5% row), §5 (`trim` column), §6 (D-27 data test), §7 (risks row), §8, §9 (item g).
- Items a–e: pending the owner's decision.
