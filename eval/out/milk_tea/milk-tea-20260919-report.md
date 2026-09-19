# Milk-tea dataset local evaluation — 2026-09-19

Dataset from branch `feat/milk-tea-dataset` (`0032bcd8e8d20788cc268b1c06efa33dd01d9772`,
remote `LinxuanLi-DS/NEU_harness_hackathon`), merged into `dev`. Unlike the Yingzi
question set, this is a **separate database** with its own schema, seed, defects and
questions, selected with `HARNESS_DATASET=milk_tea`. Results are written to
`eval/out/milk_tea/` so the SaaS numbers are untouched.

**These are new inference runs on dev, not copied from the branch.** The branch shipped
the fixture and its gold verification but explicitly made no model-accuracy claim; this
is the first A/B on it.

Qwen3.5-9B Q4_K_M; thinking disabled; curated knowledge; model at 127.0.0.1:8080;
MySQL 8.0.35 at 127.0.0.1:3307, database `milk_tea`. Both model queries and gold
queries use the SELECT-only `harness_ro` account. No cloud inference was used.

## Validation before the run

| Check | Result |
|---|---|
| `data.milk_tea.generate --check` (artifact drift) | passed — `milk-tea-1.0.0`, 10000 rows, 8 defects, 20 questions |
| Loaded row counts vs `manifest.json` | 10000/10000, every table exact |
| `tests/test_milk_tea.py` with `MILK_TEA_TEST_DB=1` | 70 passed, 0 skipped |
| Existing SaaS suite (`--ignore=tests/test_milk_tea.py`) | 198 passed, 7 skipped |
| Gold dry run (`--arm dry`) | 20/20 |
| `pip check` | no broken requirements |

The 70/0 and 20/20 figures reproduce the branch author's own `VALIDATION.md` record.
Every gold value I measured on my load matched their published table (MTQ01 121,217;
MTQ05 21,957.00; MTQ07 5,620,000; MTQ09 994,473.98; MTQ11 573,200; MTQ13 499.7500;
MTQ14 250.6060; MTQ20 6,125,768), so the fixture imported faithfully.

## Results

| Arm | Grader passes | Passes without recorded agent error | Time |
|---|---:|---:|---:|
| baseline | 6/20 (30.0%) | 6/20 | 27.0 s |
| harness | 15/20 (75.0%) | 15/20 | 246.4 s |

Lift: **+45.0 points**. Median 4 steps, median 8.0 s/question in the harness arm;
tool use was `execute_sql`=35, `profile_column`=27, `resolve_term`=15. Token totals
were 42,892 (baseline) and 487,585 (harness) — the harness costs roughly 11x the
tokens and 9x the wall time for those 9 extra correct answers.

### Per-defect

| Defect | What it is | Baseline | Harness |
|---|---|---:|---:|
| MT01 | box/cup mixing, per-SKU box size | 0/3 | 2/3 |
| MT02 | draft/void rows, per-system status codes | 1/3 | 2/3 |
| MT03 | legacy returns signed negative, ERP positive | 0/2 | **0/2** |
| MT04 | duplicated ETL replay rows | 0/3 | 1/3 |
| MT05 | header total repeated on every line | 2/2 | 2/2 |
| MT06 | production/return mirrored into stock_in | 0/3 | 1/3 |
| MT07 | `N/A` and empty strings in weight text | 0/2 | 2/2 |
| MT08 | posted rows missing `posted_at` | 0/2 | 2/2 |
| control | no defect involved | 3/3 | 3/3 |

MT07 and MT08 went 0/2 → 2/2; MT03 is the one defect class the harness did not move at all.

### The five harness failures

| Question | Gold | Harness answer | Note |
|---|---:|---:|---|
| MTQ05 | 21,957.00 | 20,097.00 | exactly the dataset's documented naive answer |
| MTQ06 | 2,876.000 | 11,490.000 | neither gold nor naive (naive is 2,636) |
| MTQ07 | 5,620,000 | 6,020,000 | exactly the documented naive answer |
| MTQ12 | 6,196,076 | 6,596,076 | neither gold nor naive (naive is 6,769,276) |
| MTQ20 | 6,125,768 | — | hit the 12-step limit, no final answer |

MTQ05 and MTQ07 are the informative ones: the harness did not merely get them wrong,
it produced the precise wrong number the dataset was built to elicit — it kept the
legacy negative-sign convention on returns, and it counted replayed stock-in rows
without deduplicating on `movement_key`. The curated glossary states both rules, so
these are retrieval-or-application failures, not missing-knowledge failures.

Baseline fell into the documented naive trap on MTQ07 (6,020,000), MTQ13 (`N/A`),
MTQ15 (1,843) and MTQ16 (357). MTQ20 failed in both arms — baseline with MySQL error
1111, harness by exhausting its steps.

Scores use the existing execution-match grader. This is one run, not an independent
audit of semantic correctness; the error-free column excludes recorded errors and
step-limit cases but does not prove final-answer correctness. Numbers are not
comparable with the 31-question or 35-question SaaS sets — different database,
different questions, different defects.

## Run again

From the dev repository root, with local MySQL and llama.cpp running, `.env`
configured, and the fixture imported (`python -m data.milk_tea.load --database milk_tea`):

```powershell
$env:HARNESS_DATASET = 'milk_tea'
$env:DB_NAME = 'milk_tea'
$env:HARNESS_LLM = 'local'
$env:LOCAL_BASE_URL = 'http://127.0.0.1:8080/v1'
$env:LOCAL_MODEL = 'qwen3.5-9b'
$env:LOCAL_ENABLE_THINKING = 'false'
$env:HARNESS_KNOWLEDGE = 'curated'
.venv\Scripts\python.exe -B eval\run.py --arm both --tag milk-tea-repeat
.venv\Scripts\python.exe -B eval\report.py --provider local --tag milk-tea-repeat
```

To view these saved results without any inference:

```powershell
$env:HARNESS_DATASET = 'milk_tea'
.venv\Scripts\python.exe -B eval\report.py --provider local --tag milk-tea-20260919
```

Unset `HARNESS_DATASET` (or set it to `saas`) to return to the original benchmark.
Runtime settings, grants, row counts and artifact hashes are in
`milk-tea-20260919-metadata.json`; the console transcript is in
`milk-tea-20260919.log`. The committed `web/static/data.js` is still the SaaS
offline snapshot — these milk-tea numbers are **not** in it. View them with a live
`python -m web.server` after selecting the dataset.
