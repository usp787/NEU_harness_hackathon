# Yingzi-Zhou local evaluation — 2026-09-19

Branch commit: `45ff06bb0f44beccc422fe4cd0545b6a017f1f5b`.
The question-set changes are Q14/Q15 revised and Q26–Q29 added. On dev this exact question set is stored as `data/questions_yingzi.yaml`. It shares the original schema and seed data. These results were copied from the branch worktree; they are the original run, not a new inference run on dev.

Qwen3.5-9B Q4_K_M; thinking disabled; curated knowledge; model at 127.0.0.1:8080; MySQL 8.0.35 at 127.0.0.1:3307. Both model queries and gold queries use the SELECT-only harness_ro account. No cloud inference or shared Wi-Fi connection was used.

Validation: 35/35 gold-query dry run; question tests: 82 passed, 9 skipped.

| Arm | Grader passes | Passes without recorded agent error | Time |
|---|---:|---:|---:|
| baseline | 18/35 (51.4%) | 18/35 | 43.1 s |
| harness | 26/35 (74.3%) | 26/35 | 317.2 s |

## Revised and added questions

| Question | Baseline | Harness |
|---|---|---|
| Q14 | FAIL | FAIL |
| Q15 | FAIL (agent error) | FAIL |
| Q26 | FAIL | FAIL |
| Q27 | FAIL | FAIL (agent error) |
| Q28 | FAIL | FAIL |
| Q29 | FAIL | FAIL |

Scores use the branch's existing execution-match grader. This is one run, not an independent audit of semantic correctness. The error-free count excludes recorded errors/step-limit cases but does not prove final-answer correctness. Q27/Q28 baseline outputs matched the reported company/count or revenue except for company-name casing and were graded as failures. Harness Q27 hit the 12-step limit; harness Q28 returned the expected revenue but used quartzsystems instead of quartz systems. Older 31-question scores are not directly comparable with this revised 35-question set.

## Run again

From the dev repository root, with the local MySQL and llama.cpp services running and database credentials configured in `.env`:

```powershell
$env:HARNESS_LLM = 'local'
$env:LOCAL_BASE_URL = 'http://127.0.0.1:8080/v1'
$env:LOCAL_MODEL = 'qwen3.5-9b'
$env:LOCAL_ENABLE_THINKING = 'false'
$env:HARNESS_KNOWLEDGE = 'curated'
$env:DB_HOST = '127.0.0.1'
$env:DB_PORT = '3307'
.venv\Scripts\python.exe -B eval\run.py --questions data/questions_yingzi.yaml --arm both --tag yingzi-repeat
.venv\Scripts\python.exe -B eval\report.py --provider local --tag yingzi-repeat
```

To view the saved results without any inference:

```powershell
.venv\Scripts\python.exe -B eval\report.py --provider local --tag yingzi-20260919
```

To validate the question queries without inference, use `--arm dry` with the same `--questions` argument and a fresh `--tag`. The default `data/questions.yaml` is unchanged. Alternate question files automatically use their filename stem as the output tag when no explicit tag is supplied, preserving the default results. New runs record the question-file path and SHA-256 in their output. The original saved JSON files remain byte-for-byte copies from the worktree; their source commit and runtime settings are in `yingzi-20260919-metadata.json`.
