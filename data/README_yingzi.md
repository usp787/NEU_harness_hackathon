# Yingzi's question set

`questions_yingzi.yaml` is an exact copy of `data/questions.yaml` from
`Yingzi-Zhou` commit `45ff06bb0f44beccc422fe4cd0545b6a017f1f5b`.
It contains 35 questions: Q14/Q15 revise company normalization and Q26-Q29
add four company-level questions. It uses the existing `schema.sql` and
`seed.sql`; no separate database import is needed.

The existing runner accepts `--questions data/questions_yingzi.yaml`.
The original 31-question `questions.yaml` remains the default.

See [the saved run and commands](../eval/out/yingzi-20260919-report.md).
The saved baseline/harness scores are 18/35 and 26/35 using local Qwen3.5-9B
with curated knowledge. They were copied from the prior worktree run,
not regenerated after adding this file to dev.
