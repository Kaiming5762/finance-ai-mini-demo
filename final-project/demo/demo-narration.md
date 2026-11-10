# 5-minute demo - verbatim narration and pre-flight checklist

Companion to `demo-script.md` and `demo-slides.html`. Use this as the teleprompter.

**Language:** `[SAY]` blocks are the verbatim English script, matching the English
slides, report and course brief. Read them aloud as written; do not translate
during the take. `[ON SCREEN]` blocks are Chinese directions for the operator.
**Timing:** ~140 words/minute. Each segment has a hard cue; if you are late,
apply the compression plan at the end instead of speeding up.
**Integrity:** single take, no edits. State "live" or "recorded" at 0:00 and in
the submission text. Never present a recorded run as live.

---

## 0:00 - 0:45 | Slide 1 / 5 | The user task

`[ON SCREEN]` 从 `demo/` 目录双击打开 `demo-slides.html`，停在第 1 页；用文件管理器把
`offers_case_A.csv` 和 `borrower_case_A.json` 展示约 10 秒，然后回到幻灯片。

`[SAY]`
> Hi - this is a five-minute live demonstration of Loan Offer Compass, my final
> project on Loans and financing. It is a single-take run with no edits. Here is
> the user problem: a borrower has four HKD 180,000 personal-loan quotations with
> different nominal rates, arrangement fees, terms and repayment structures, and
> a hard ceiling of HKD 6,000 a month. Which offer is genuinely cheapest, among
> the ones they can actually afford? These two files are the documented inputs:
> an offers CSV and a borrower JSON. All numbers are synthetic teaching data,
> not real bank quotes. Everything runs on the Python standard library - no
> installs, no network, no API key.

*If recorded, replace the second sentence with: "This is a recording made on
10 November 2026; it is labelled recorded, not live."*

---

## 0:45 - 1:45 | Slide 2 / 5 | Core output from a real tool run

`[ON SCREEN]` 终端执行 `python scripts/run_all.py --only case_A`，让 stdout 完整停在屏幕上
（4 offers / 0 errors / 7 of 7 checks）。切到第 2 页，指表格高亮行和两张图；有余量可开
`outputs/case_A/comparison.md` 两秒。

`[SAY]`
> Let me actually run it, rather than show you a chat message. One command runs
> the engine and the independent checker. Watch the real stdout: four offers,
> zero validation errors, zero duplicate IDs, and a binding ceiling of 6,000.
> Each offer gets a peak monthly outflow, an all-in cost, an effective APR and
> EAR, an affordability verdict, and seven out of seven internal identity
> checks. Here is the result on slide two. The naive shortcut picks A1, because
> 5.2 percent is the lowest advertised rate - but its 2.5 percent arrangement
> fee lifts the effective APR to 6.9 percent. The cheapest affordable offer is
> actually A2, at HKD 18,016 all-in and 6.3 percent APR. A3 has the lowest total
> cost of all four, HKD 13,026, but its HKD 8,043 monthly instalment breaks the
> cap, so it must be excluded. The two charts show the balance paths and where
> the cost comes from. Full tables are in comparison.md.

---

## 1:45 - 3:00 | Slide 3 / 5 | One important, independent check

`[ON SCREEN]` 终端执行：
```
python skills/loan-offer-comparison/scripts/verify.py --offers skills/loan-offer-comparison/examples/offers_case_A.csv --config skills/loan-offer-comparison/examples/borrower_case_A.json --out outputs/case_A --report outputs/case_A/verification.md
```
把 `83/83 checks passed, 0 failed` 留在屏幕上；切第 3 页，指四个卡片；再开
`outputs/case_A/verification.md` 指已知答案、独立月供、独立 IRR 三行。

`[SAY]`
> A green number means nothing unless the check is independent. So verify.py
> does not rerun the engine's formulas. It re-reads the saved schedule CSVs,
> finds the level payment by bisection on a recursive balance equation instead
> of the closed-form annuity, and solves the IRR with Newton's method and an
> analytic derivative instead of the engine's bisection. Let me run it.
> Eighty-three out of eighty-three checks pass, zero failures. Three rows I
> want to point at: the known-answer case, ten thousand at twelve percent over
> twelve months, gives 888.487886783, the same as a spreadsheet PMT. A2's
> payment is 5,500.449578 by both methods. A1's monthly IRR is 0.069003688 by
> both methods. The battery also covers six changed inputs, eight malformed
> CSVs and one CLI error-behaviour case. Bad inputs stop with exit code three
> and write no output; they are never silently dropped. One honest note: the
> very first verification failed - eleven out of twelve, with a Newton
> convergence bug. I fixed the stopping rule, and both the failure and its
> correction are kept in the report. The checker can genuinely fail.

---

## 3:00 - 4:00 | Terminal only (no slide) | Changed inputs

`[ON SCREEN]` 复制 `offers_case_A.csv` 为 `demo/demo_changed.csv`，只把 A1 的
`0.0520` 改成 `0.0620`，然后执行：
```
python skills/loan-offer-comparison/scripts/loan_compare.py --offers demo/demo_changed.csv --config skills/loan-offer-comparison/examples/borrower_case_A.json --out outputs/demo_changed
```
对比 A1 的 peak/month 与 APR 都上升。再执行
`python skills/loan-offer-comparison/scripts/verify.py --battery-only --report demo/battery.md`
展示 changed / invalid 输入行。时间紧时只跑第二条。

`[SAY]`
> Now a changed-input check - the part that shows the result is not a cached
> answer. I copy the offers file and change exactly one cell: A1's rate from
> 5.2 to 6.2 percent, and I send the output to a brand-new folder. As expected,
> A1's monthly payment and its effective APR both move up; the ranking is
> recomputed, not recalled. I can also run the whole evaluation battery on its
> own: six changed-input cases covering rate, upfront fee, term, monthly fee,
> budget cap and repayment structure, plus eight invalid-input cases. If I feed
> it a malformed CSV, it stops immediately with an explicit input error and
> exit code three, and it does not create the output folder. That is the
> "check before analysing" rule: reject bad data loudly.

---

## 4:00 - 4:45 | Slide 4 / 5 | Reusable Skill on a fresh case

`[ON SCREEN]` 打开 `skills/loan-offer-comparison/SKILL.md` 扫过 YAML 头与各节标题（约 8 秒）。
**先确认** `outputs/demo_fresh` 不存在，再执行：
```
python scripts/run_all.py --only case_B --case-b-out outputs/demo_fresh
```
展示 stdout 的 83/83 与 naive-vs-APR disagreement；切第 4 页。

`[SAY]`
> The reusable contribution is a regular Skill: SKILL.md with its name,
> description, scope, inputs and outputs, the financial definitions, the
> six-part procedure, checks, failure handling and limitations, plus runnable
> scripts and examples. No hard-coded personal path, secret, cached answer or
> previous approval. To show it generalises, I run a completely different case:
> a CNY 600,000 SME equipment loan, 48 and 60-month terms, a CNY 12,000 cap,
> into a new empty output folder. Again eighty-three out of eighty-three checks
> pass, and again the naive lowest-rate pick disagrees with the lowest effective
> APR. I label this honestly as self-reproduction by the same author - it is
> not a classmate's independent reuse test.

---

## 4:45 - 5:00 | Slide 5 / 5 | Where it lives and one limitation

`[ON SCREEN]` 切第 5 页，指仓库链接、openJiuwen 链接和 Limitations 卡片；口播结束立刻停录。

`[SAY]`
> Everything is public at Kaiming5762/finance-ai-mini-demo under final-project,
> with the exact commit URL in the contribution record and the openJiuwen link
> in the README. Main limitation: monthly instalments only, nominal
> undiscounted all-in cost, synthetic data. Takeaway - the lowest advertised
> rate is not the cheapest loan. Thank you.

---

# Pre-flight checklist

## A. One day before

- [ ] `cd final-project` then `python --version` (3.9+; tested 3.13.14).
- [ ] `python scripts/run_all.py` - both cases PASS, `evidence/E1`-`E4` exist,
      `outputs/*/verification.md` each say **83/83 checks passed, 0 failed**.
- [ ] Open `demo/demo-slides.html` **from the `demo/` folder** and page through
      all 5 slides; confirm both SVG charts render (they use `../outputs/...`).
- [ ] Confirm `report/report.pdf` (9 pages) and `final-project_source.zip` exist.
- [ ] Rehearse once with a stopwatch; target 4:45-5:10, never over 5:15.

## B. 30 minutes before

- [ ] Close mail, chat, browsers with personal tabs, password managers, cloud
      sync popups. Turn on Do Not Disturb. **No credentials, tokens or key
      files anywhere on screen** (also see `demo-script.md`).
- [ ] Screen: 1920x1080 or 1080p recording; terminal font >= 16 pt; browser
      zoom 125%; disable auto-hide taskbar.
- [ ] Audio: microphone test, 10-second sample, no fan/traffic noise; know the
      record/stop shortcut.
- [ ] Prepare a plain-text `demo/commands.txt` with the 4 commands above so you
      copy-paste instead of typing live (optional but strongly recommended).
- [ ] Decide and write down: **live** or **recorded** + recording date.

## C. 5 minutes before

- [ ] Terminal already in `final-project`; `python --version` visible.
- [ ] Slides open on slide 1, charts pre-loaded (scroll down once then back up).
- [ ] `outputs/demo_changed` and `outputs/demo_fresh` **do not exist** - the
      "new empty folder" claim must be literally true on camera.
- [ ] `demo/demo_changed.csv` prepared with A1 rate `0.0620`; check with
      `head -2 demo/demo_changed.csv`.
- [ ] Timer/stopwatch visible but not covering the terminal output.
- [ ] Water, silence phone, close the door.

## D. Last 60 seconds

- [ ] Start recording, then say the live/recorded declaration at 0:00.
- [ ] One deep breath; speak at ~140 wpm; do not speed up if behind - compress.
- [ ] Keep the real stdout on screen for at least 3 seconds at each cue.

## E. Self-check at each time cue

| Cue | Ask yourself |
|---|---|
| 0:45 | Did I say "synthetic data" and state live/recorded? |
| 1:45 | Is a **real tool stdout** on screen, not chat text? Are A1/A2/A3 numbers correct? |
| 3:00 | Did I say 83/83 **and** the first 11/12 failure? |
| 4:00 | Did bad inputs get "exit code 3, no output", not "silently dropped"? |
| 4:45 | Did I run Case B into a **new empty folder** and say "self-reproduction"? |
| 5:00 | Did I name one limitation and the repo URL? |

## F. After stopping the recording

- [ ] Duration 4:45-5:15; audio clear; terminal text legible at 1080p.
- [ ] Watch once for accidental exposure: no credentials, tokens, personal
      financial data, private tabs or absolute home paths in view.
- [ ] Name the file clearly, e.g. `loan-offer-compass-demo-2026-11-10.mp4`.
- [ ] In the submission text, write "live" or "recorded on <date>" to match
      what you said at 0:00. Do not relabel.
- [ ] Keep the video **outside** the repository unless the course asks for it.
- [ ] Tidy the demo-only artefacts if you want a clean working tree:
      `demo/demo_changed.csv`, `demo/battery.md`, `demo/commands.txt`,
      `outputs/demo_changed/`, `outputs/demo_fresh/`. Keep `evidence/E1`-`E4`
      and the two `outputs/` case folders - those are submission evidence.

## G. Contingencies

| Problem | Action |
|---|---|
| Running late at 3:00 | Skip the single-cell CSV edit; run `--battery-only` only (25 s). |
| Running late at 4:00 | Shorten SKILL.md tour to 3 s; keep the fresh-case execution - it is mandatory. |
| A command fails live | Do not fake it. Say "I'll use the saved execution evidence", open `evidence/E1`-`E4`, and continue; note the hiccup honestly. |
| Charts blank in slides | They are relative paths: reopen the HTML from `demo/`, or hard-refresh. Never claim a chart is there if it is not. |
| Verbal slip | Keep going. Single take, no edits; a small slip is more honest than a splice. |
| 5:15 hard cutoff | Cut the 3:00-4:00 segment; never cut the independent check or the fresh-case run. |

## H. Never say during the demo

- "A classmate reused my Skill" (it is self-reproduction only).
- "This is a real bank quote" (data are synthetic).
- "This is a WorkSwarm UI screenshot" (evidence is local tool output; see
  `report/report.pdf` section 3 for the honest labelling).
- "Hub submission / upstream PR was completed" (optional routes, not attempted).
