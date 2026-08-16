# Annotation Quality Standard

## 1. Read before selecting

Read enough surrounding material to understand the claim. At minimum inspect
the abstract, introduction, method overview, experiment setup, results, and
limitations relevant to the project. A figure caption can be highlighted when
it is the clearest full explanation, but never infer the paper's whole claim
from a figure alone.

## 2. English highlight

A highlight must:

- reproduce exact, contiguous PDF text;
- cover at least one complete grammatical sentence;
- express one self-contained concept worth revisiting;
- include necessary qualifiers such as dataset, comparison, metric, or
  limitation;
- normally contain one to four sentences and remain on one PDF page because
  the current geometry locator matches within a page;
- be long enough to understand without pasting unrelated surrounding text.

Do not highlight:

- a single word, heading, keyword, or sentence fragment;
- a large paragraph when only one sentence matters;
- a claim whose essential qualifier has been omitted;
- text selected only because it contains `gaze`, `world model`, `belief`, or
  another project keyword;
- non-contiguous excerpts combined into one quote.

If a useful paragraph crosses a page boundary, select a complete sentence on
one page or represent the two parts as separate concepts.

## 3. Vietnamese explanatory note

Write for a reader who has not mastered the field. Keep important English
terms in place and explain them on first use. A good note usually contains:

1. **Plain meaning:** what the passage says in accessible Vietnamese.
2. **Terminology:** what unfamiliar terms mean operationally, not just a
   Vietnamese synonym.
3. **Evidence or mechanism:** what was measured, compared, predicted, or
   changed.
4. **Project relevance:** how it connects to gaze, partial observation,
   belief/state update, prediction, planning, or evaluation when relevant.
5. **Claim boundary:** what the passage does not establish and what evidence
   would still be needed.

Do not assume the reader already understands terms such as `fixation`,
`scanpath`, `saliency`, `POMDP`, `belief state`, `latent state`,
`action-conditioned`, `counterfactual`, `causal`, `linear probe`, or
`closed-loop control`.

Example style:

> `Scanpath` là chuỗi fixation theo thứ tự không gian và thời gian, không chỉ
> là một heatmap cho biết vùng nào nổi bật. Kết quả này cho thấy đúng alignment
> giữa semantic information và gaze có ích cho việc dự đoán scanpath.
>
> Liên hệ benchmark: logic này gần với TRUE_GAZE so với SHUFFLED_GAZE. Tuy
> nhiên, scanpath similarity chưa chứng minh gaze đã cải thiện hidden-state
> prediction hoặc downstream decision; cần đo trực tiếp các outcome đó.

## 4. Number and coverage

There is no universal fixed count. Prefer approximately three to six strong
concepts per ordinary paper. Use more only when distinct passages are directly
important. Across a paper, prioritize:

- problem definition or formalization;
- method mechanism;
- evaluation protocol and baselines;
- strongest result with its qualifier;
- limitation or failure mode;
- the exact overlap with, and gap left for, the proposed benchmark.

Three insightful annotations are better than ten redundant ones.

## 5. Critical reading

Distinguish these claims:

- predicting human gaze;
- using gaze as an input or supervision signal;
- selecting visual evidence actively;
- maintaining a belief about hidden state;
- predicting action-conditioned futures;
- supporting planning or downstream control.

Success at an earlier item does not automatically prove a later one. Notes
should state this boundary explicitly whenever authors use broad terms such as
`world model`, `reasoning`, `causal`, or `active perception`.
