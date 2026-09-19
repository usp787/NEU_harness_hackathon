# Mixed five-industry dataset — local evaluation, 2026-09-19

Dataset from branch `mixed-dataset` (`6e30845da54e6845ee87b119436ac5c7fd33bbc9`,
remote `usp787/NEU_harness_hackathon`). Five industry datasets (medical, legal,
e-commerce, short-video, maps) condensed into **one database: 25 prefixed tables,
27,761 rows, 30 questions, 10 defects (D1–D10)**. Selected with
`HARNESS_DATASET=mixed DB_NAME=mixed`; results land in `eval/out/mixed/` so the
SaaS and milk-tea numbers are untouched.

**These are new inference runs on dev, not copied from the branch.** The branch
shipped the fixture and its gold verification and explicitly made no
model-accuracy claim ("没有读 harness 代码，也没跑过 `eval/run.py`"). This is the
first A/B on it.

Qwen3.5-9B Q4_K_M; thinking disabled; model at 127.0.0.1:8080 with
**`-c 16384`** (see *Context budget* below); MySQL 8.0.35 at 127.0.0.1:3307,
database `mixed`. Both model and gold queries use the SELECT-only `harness_ro`
account. No cloud inference was used.

## Read this before quoting the number

`mixed` ships **no curated glossary**. On SaaS and milk-tea, `HARNESS_KNOWLEDGE=curated`
hands the harness a hand-written set of business terms; on `mixed` there is
nothing to hand it, so `active_glossary()` returns 0 terms. The harness arm below
therefore ran **structure-only** — schema card, column profiling, join hints and
the `execute_sql` tool loop, with no business-knowledge layer.

That makes this a measurement of the harness's *structural* half. It is not
comparable to the milk-tea 6/20 → 15/20 headline, which was measured with a
curated glossary. A curated run on `mixed` is the obvious next experiment and
would need someone to write the terms first; the branch README already lists
which defects need per-industry wording (D7, D9, D10).

## Integration work this required

The branch deliberately left harness code untouched and its README suggested
copying `mixed/questions.yaml` and `mixed/defects.yaml` over the files in
`data/`. That was not done — it is destructive and makes runs incomparable.
`mixed` was registered as a proper third dataset instead. Two latent bugs
surfaced in the process, both of which would have corrupted this run:

| Bug | Effect if unfixed |
|---|---|
| `active_glossary()` and `execute.py`'s hint branch fell back to the **saas** glossary for any unrecognised dataset | The harness arm would have been told `plan_tier` is a stale cache and `cust_id` has orphan rows — in a database with neither column. Confident nonsense, not a neutral no-op. |
| `report.py`'s `DEFECT_ORDER` assumed any non-saas dataset used milk-tea's `MT01–MT08` ids | `mixed` uses `D1–D10`, so no id would have matched and the entire per-defect table would have rendered **blank rather than erroring** — the most persuasive artifact silently absent. |

Both are now dataset-scoped: saas terms fire only on saas, and the defect order
is read from each dataset's own `defects.yaml`.

## Validation before the run

| Check | Result |
|---|---|
| `mixed/generate.py --check` (artifact drift) | passed — `seed.sql is up to date` |
| Loaded schema | 25 tables, 27,761 rows, all five prefixes (`med_ leg_ ecom_ tt_ map_`) |
| Gold dry run (`--arm dry`) | **30/30** |
| Full existing suite (`pytest tests/`) | 225 passed, 50 skipped — unchanged before and after the integration |
| Dataset routing (saas / milk_tea / mixed) | db, data dir, results dir and curated-term count correct for each; saas still 12 terms, milk_tea still 7, mixed 0 |

## Results

| Arm | Passes | Context overflows | Graded | Tokens | Time |
|---|---:|---:|---:|---:|---:|
| baseline | 18/30 (60.0%) | 0 | 30/30 | 103,322 | 33.6 s |
| harness | 21/30 (70.0%) | 0 | 30/30 | 1,064,025 | 243.2 s |

Lift: **+10.0 points**. Median 4 steps and 6.3 s/question in the harness arm;
tool use was `profile_column`=48, `execute_sql`=36, `resolve_term`=30. The
harness cost roughly **10x the tokens and 7x the wall time for 3 extra correct
answers** — a markedly worse trade than milk-tea's 11x tokens for 9 answers,
which is what running without a glossary buys you.

Note `resolve_term` was called 30 times against an empty glossary. Those calls
could only ever return "no convention known", so a meaningful slice of the
harness arm's token cost bought nothing here.

### Per-defect

| Defect | Baseline | Harness | Lift | What it is |
|---|---:|---:|---:|---|
| D1 | 3/3 (100%) | 2/3 (67%) | **−33 pts** | 同一概念的字段命名不一致 |
| D2 | 2/2 (100%) | 2/2 (100%) | +0 pts | 同名列，取值域不同 |
| D3 | 0/2 (0%) | 0/2 (0%) | +0 pts | 冗余列与真实来源不一致（过期缓存） |
| D4 | 3/3 (100%) | 3/3 (100%) | +0 pts | NULL 含两种互不兼容的含义 |
| D5 | 1/3 (33%) | 3/3 (100%) | **+67 pts** | 数值以文本存储，混有非数值内容 |
| D6 | 1/2 (50%) | 1/2 (50%) | +0 pts | 同一真人用不同账号重复注册 |
| D7 | 0/2 (0%) | 0/2 (0%) | +0 pts | 混合时区，没有时区列 |
| D8 | 2/3 (67%) | 3/3 (100%) | **+33 pts** | 孤儿外键，未声明约束 |
| D9 | 1/2 (50%) | 2/2 (100%) | **+50 pts** | 枚举值超出文档范围 |
| D10 | 0/3 (0%) | 0/3 (0%) | +0 pts | 金额单位混用 |
| control | 5/5 (100%) | 5/5 (100%) | +0 pts | (control — no defect involved) |

Controls held at 5/5 in both arms, so the harness is not costing accuracy on
clean questions.

### What the harness fixed, and what it did not

**Fixed (D5, D8, D9 — +6 questions):** exactly the defects that column
*profiling* exposes. D5 is numbers stored as text with junk mixed in, D8 is
orphan foreign keys, D9 is enum values outside the documented range. All three
are visible by looking at the data, which is what `profile_column` does and what
the baseline never gets to do. This is the structural half of the harness working
as designed, with no glossary needed.

**Untouched (D3, D7, D10 — 0/7 in both arms):** these need knowledge that is not
in the data. D10 is mixed currency units, D7 is mixed timezones with no timezone
column, D3 is a stale cache column disagreeing with its source. Profiling shows
the values; nothing in the values says which unit, which zone, or which column to
distrust. This is precisely the gap a curated glossary fills, and its absence
here is the cleanest evidence in this run that the glossary is load-bearing
rather than decorative — the harness's structural tooling alone cannot touch
these three, and on milk-tea with a glossary the comparable defects moved.

**Regressed (D1, 3/3 → 2/3):** the only regression. Q01 returned 78 against a
gold of 80. D1 is inconsistent field naming for the same concept — the one defect
class where the baseline's naive reading of the DDL happened to be right, and the
harness's extra exploration talked it out of a correct answer without a glossary
term to anchor on. Worth a look before this dataset is used for anything load-bearing.

### Harness failures (9)

| Q | Defect | Gold | Got |
|---|---|---|---|
| Q01 | D1 | 80.0 | 78.0 |
| Q04 | D7 | 56.0 | 48.0 |
| Q05 | D10 | 164.4301 | 164.6263 |
| Q07 | D3 | 50024.0 | wrong shape — returned 4 columns incl. date/status/type |
| Q08 | D6 | 57.0 | 65.0 |
| Q15 | D10 | 430311.6 | 12190420.0 |
| Q17 | D3 | 5000011.0 | wrong shape — returned 2 columns |
| Q20 | D10 | 1247.693 | 45936.29 |
| Q24 | D7 | 41.0 | 52.0 |

The three D10 misses are order-of-magnitude wrong (Q15 is 28x, Q20 is 37x),
consistent with summing mixed currency units without converting. Q07 and Q17
(both D3) failed on result *shape* rather than value — the model returned extra
columns instead of only what was asked, which the grader treats as a mismatch.

## Context budget

This run was the first on `-c 16384`, reduced from 32768 earlier the same day to
free VRAM. The mixed dataset was the stress case, since its 25-table schema is
much larger than any single dataset's and the branch README flagged the context
pressure as its main unknown.

| | Value |
|---|---|
| Context budget | 16,384 |
| Peak prompt observed (168 requests) | **9,290** |
| p50 / p90 / p99 | 7,647 / 8,211 / 9,055 |
| Context overflows | **0** |

Headroom at the peak was 1.76x. The 25-table schema did **not** blow up the
context as feared: peak here (9,290) is actually *lower* than the 11,328 measured
on the smaller SaaS/milk-tea schemas, because the harness builds a selective
schema card rather than dumping all DDL. The median is higher (7,647 vs ~5,000),
so mixed is consistently heavier but has a tighter tail.

Both arms report `context_overflow: 0` and `graded: 30/30`, so `accuracy` and
`accuracy_graded` agree and the percentages above are clean. That accounting is
new in this run — an overflow previously surfaced as an opaque `400 Bad Request`
and was counted as an ordinary wrong answer, which would have quietly deflated
any number measured at a reduced context.

## Reproducing

```bash
docker compose exec -T mysql mysql -uroot -phackathon \
  -e "CREATE DATABASE IF NOT EXISTS mixed CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
docker compose exec -T mysql mysql -uroot -phackathon mixed < mixed/seed.sql
docker compose exec -T mysql mysql -uroot -phackathon \
  -e "GRANT SELECT ON mixed.* TO 'harness_ro'@'%'; FLUSH PRIVILEGES;"

.\scripts\setup-local-model.ps1 -StartOnly -CtxSize 16384

HARNESS_DATASET=mixed DB_NAME=mixed .venv/Scripts/python eval/run.py \
  --arm dry  --tag mixed-20260919
HARNESS_DATASET=mixed DB_NAME=mixed .venv/Scripts/python eval/run.py \
  --arm both --tag mixed-20260919
HARNESS_DATASET=mixed DB_NAME=mixed .venv/Scripts/python eval/report.py \
  --tag mixed-20260919
```

On Windows the report table's Chinese defect titles render as mojibake in the
console (codepage, not data — the YAML and this file are UTF-8). Read them here
or pipe through a UTF-8 terminal.
