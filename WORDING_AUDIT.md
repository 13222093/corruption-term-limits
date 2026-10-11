# WORDING_AUDIT.md: neutral wording about Lee et al. (2019)

Scope: every document and code comment that describes how our reading of Lee, Iwasa, Dieckmann
and Sigmund (2019) and its SI differs from the printed text. Goal: describe these as notation
inconsistencies that we resolved, credit the original authors, and keep item D5 (our own
misreading, withdrawn after reading the SI) only in the change logs CHANGES_SI.md and
DECISIONS.md, plus one reminder in the author's private notes, as the release task asks.

Method: searched for error, mistake, wrong, typo, fail, misnamed, misread, swapped, reversed,
slip, lost minus signs, contradict, incorrect, inconsistency, discrepancy and D5 in the paper
sources, the Markdown templates in docs_src/, SPEC.md, SI_EXTRACT.md, figures/README.md,
METRICS.md, CITATIONS_TODO.md, src/, experiments/ and tests/. Generated Markdown files (README.md,
FINAL_REPORT.md, REVIEW.md, CHANGES_SI.md) are rendered from the templates, so they change with them. Uses of these words about our own
code, our tests or statistical errors were left as they are.

## Files changed

| File | Replacements |
|---|---|
| `paper/main.tex` | 12 |
| `paper/ieee/main_ieee.tex` | 13 |
| `docs_src/README.md.in` (and its rendered output) | 11 |
| `docs_src/FINAL_REPORT.md.in` (and its rendered output) | 4 |
| `docs_src/REVIEW.md.in` (and its rendered output) | 3 |
| `docs_src/CHANGES_SI.md.in` (and its rendered output) | 5 |
| `SPEC.md` | 8 |
| `SI_EXTRACT.md` | 12 |
| `experiments/digitize_si.py` | 1 |
| `tests/test_fixed_points.py` | 1 |
| `tests/test_rare_exploration.py` | 1 |

The author's private notes (interview notes, statement-of-purpose sentences and a CV entry)
were audited in the same way; they are no longer part of the repository (DECISIONS D-026).
Paper sections added: Acknowledgements in both papers now credit the original
authors and disclose AI assistance.

## Phrases replaced, by file

### `paper/main.tex`

| Before | After | Note |
|---|---|---|
| We reproduce the paper's analytical benchmarks exactly and its simulations closely, and we document six inconsistencies in the paper and its supplementary information. | We reproduce the paper's analytical benchmarks exactly and its simulations closely. | abstract: discrepancies no longer listed in the abstract |
| and their simulations closely. We document six inconsistencies in the paper and its SI, none of which changes the paper's conclusions. | and their simulations closely. | introduction: sentence removed |
| The printed equation has the weights of $Q_H$ and $Q_C$ swapped; we use the reading that is consistent with $y$ being the honest fraction (Appendix~\ref{app:typos}). | A few notation inconsistencies in the original text, including the weighting in $Q(y)$, were resolved as described in Appendix~\ref{app:typos}. | model section: the single main-text sentence on notation inconsistencies |
| With the printed weighting of $Q(y)$, the all-corrupt case instead ends at OC $=\PrintedOC$, which contradicts the paper's own statement. | (removed) | results: moved to the appendix table (D1 evidence) |
| agrees with the published matrix except for one entry (D4) in a row that the chain never revisits, | reproduces the published matrix in every entry that affects the stationary distribution (Appendix~\ref{app:typos}), | results: D4 label removed from main text |
| We found that the time series in Lee et al.'s Fig.~3C, D match the orbit at $\mu=\nu=0.02$ (period \PerViolet; peaks of OC, PC, PD and OD \VioletOC, \VioletPC, \VioletPD{} and \VioletOD) rather than the orbit at $10^{-4}$ named in the caption, whose period is \PerSlow{} (Fig.~\ref{fig:damped}D). All discrepancies are listed in Appendix~\ref{app:typos}. | Panel D shows the orbit at $\mu=\nu=0.02$ (period \PerViolet; peaks of OC, PC, PD and OD \VioletOC, \VioletPC, \VioletPD{} and \VioletOD), whose values match the time series in Lee et al.'s Fig.~3C, D (Fig.~\ref{fig:damped}D; Appendix~\ref{app:typos}). | results: D6 described as a match, details in the appendix |
| did not change; the derivation of the transition matrix was corrected to the SI's rules for neutral mutants. | did not change; our derivation of the transition matrix now follows the SI's rules for neutral mutants. | SI appendix: describes our change, not the original |
| The SI's figure has its axis labels swapped relative to its caption (D7); the caption's assignment fits our periods. | In SI Fig.~9 the axis labels of the panels are exchanged relative to the caption (D7); we follow the caption, whose assignment fits our periods. | SI appendix: D7 neutral wording |
| Appendix title 'Reproduction notes and resolved typos'; table columns 'Issue/Resolution' with rows using 'reversed', 'swapped', 'omits', 'fails B1', 'The caption is right'; D5 row; U1 row; 'the PMC web version lost minus signs' | Appendix title 'Reproduction notes and notation inconsistencies'; introduction crediting Lee et al.; table 'Observation and evidence / How we resolved it' for D1-D4, D6, D7 with neutral wording; D5 row removed; U1 moved to text; 'the PMC web version does not display the minus signs' | reproduction appendix rewritten |
| \section*{Acknowledgements} [Placeholder.] | \section*{Acknowledgements} This reproduction relies entirely on the clear and detailed work of Lee, Iwasa, Dieckmann and Sigmund~\cite{lee2019social}, including their supplementary information. AI coding tools (Claude Code) assisted with the implementation and analysis under the author's direction. [Further acknowledgements: placeholder.] | acknowledgements: credit to the original authors and AI-assistance disclosure added |
| app:typos | app:notes | internal LaTeX label renamed (8 occurrences) |
| tab:typos | tab:notation | internal LaTeX label renamed (2 occurrences) |

### `paper/ieee/main_ieee.tex`

| Before | After | Note |
|---|---|---|
| and their simulations closely. We document six inconsistencies in the paper and its SI, none of which changes its conclusions. | and their simulations closely. | introduction: sentence removed |
| The printed equation has the weights of $Q_H$ and $Q_C$ swapped; we use the reading that is consistent with $y$ being the honest fraction (Appendix~\ref{app:typos}). | A few notation inconsistencies in the original text, including the weighting in $Q(y)$, were resolved as described in Appendix~\ref{app:typos}. | model section: the single main-text sentence on notation inconsistencies |
| With the printed weighting of $Q(y)$, the all-corrupt case instead ends at OC $=\PrintedOC$, which contradicts the statement of the original paper. | (removed) | results: moved to the appendix table (D1 evidence) |
| agrees with the published matrix except for one entry (D4) in a row that the chain never revisits, | reproduces the published matrix in every entry that affects the stationary distribution (Appendix~\ref{app:typos}), | results: D4 label removed from main text |
| confirmed its analytical results exactly, and documented six inconsistencies in the paper and its SI. | and confirmed its analytical results exactly. | conclusion: clause removed |
| did not change; the derivation of the transition matrix was corrected to the SI's rules for neutral mutants. | did not change; our derivation of the transition matrix now follows the SI's rules for neutral mutants. | SI appendix: describes our change, not the original |
| The SI's figure has its axis labels swapped relative to its caption (D7); the caption's assignment fits our periods. | In SI Fig.~9 the axis labels of the panels are exchanged relative to the caption (D7); we follow the caption, whose assignment fits our periods. | SI appendix: D7 neutral wording |
| Appendix title 'Reproduction notes and resolved typos'; table columns 'Issue/Resolution' with rows using 'reversed', 'swapped', 'omits', 'fails B1', 'The caption is right'; D5 row; U1 row; 'the PMC web version lost minus signs' | Appendix title 'Reproduction notes and notation inconsistencies'; introduction crediting Lee et al.; table 'Observation and evidence / How we resolved it' for D1-D4, D6, D7 with neutral wording; D5 row removed; U1 moved to text; 'the PMC web version does not display the minus signs' | reproduction appendix rewritten |
| \section*{Acknowledgment} [Placeholder.] | \section*{Acknowledgment} This reproduction relies entirely on the clear and detailed work of Lee, Iwasa, Dieckmann and Sigmund~\cite{lee2019social}, including their supplementary information. AI coding tools (Claude Code) assisted with the implementation and analysis under the author's direction. [Further acknowledgements: placeholder.] | acknowledgements: credit to the original authors and AI-assistance disclosure added |
| We reproduce the analytical benchmarks of the original paper exactly and its simulations closely, and we document six inconsistencies in the paper and its supplementary information. | We reproduce the analytical benchmarks of the original paper exactly and its simulations closely. | abstract: discrepancies no longer listed in the abstract |
| The time series in Lee et al.'s Fig.~3C, D match the orbit at $\mu=\nu=0.02$ (period \PerViolet; peaks of OC, PC, PD, and OD \VioletOC, \VioletPC, \VioletPD, and \VioletOD) rather than the orbit at $10^{-4}$ named in the caption, whose period is \PerSlow{} (Fig.~\ref{fig:damped}D). All discrepancies are listed in Appendix~\ref{app:typos}. | Panel D shows the orbit at $\mu=\nu=0.02$ (period \PerViolet; peaks of OC, PC, PD, and OD \VioletOC, \VioletPC, \VioletPD, and \VioletOD), whose values match the time series in Lee et al.'s Fig.~3C, D (Fig.~\ref{fig:damped}D; Appendix~\ref{app:typos}). | results: D6 described as a match, details in the appendix |
| app:typos | app:notes | internal LaTeX label renamed (8 occurrences) |
| tab:typos | tab:notation | internal LaTeX label renamed (2 occurrences) |

### `docs_src/README.md.in`

| Before | After | Note |
|---|---|---|
| The SI corrected our derivation of the rare-exploration matrix (discrepancy D5 withdrawn). | (removed; the new SI note describes what the SI states and that the rerun changed no result) | README SI note rewritten in Part 1 of the release task; D5 label removed |
| ## Reproduction notes: discrepancies and resolved typos | ## Reproduction notes: notation inconsistencies and how we resolved them The reproduction relies on the clear and detailed description of the model by Lee et al. (2019) and its SI. In a few places the printed text or figures can be read in more than one way. None of these affects the conclusions of the original paper. | heading 'discrepancies and resolved typos' replaced; credit added |
| \| ID \| Where \| Issue \| Resolution \| | \| ID \| Where \| Observation \| How we resolved it \| | table header |
| \| D1 \| Methods p.13281 \| Q(y) printed as y1 Q_C + (1 - y1) Q_H although y1 is the honest fraction (also in the PDF, not only PMC) \| Q(y) = y1 Q_H + (1 - y1) Q_C; the printed form fails B1 (test) \| | \| D1 \| Methods p.13281 \| Q(y) is printed as y1 Q_C + (1 - y1) Q_H, while y1 denotes the honest fraction (in the PDF as well as on PMC) \| We read it as Q(y) = y1 Q_H + (1 - y1) Q_C, which gives the stated results B1 and B2 (a test shows that the literal reading does not give B1) \| | D1: 'the printed form fails B1' replaced |
| \| D2 \| Methods p.13281 \| Honest mixed state called "OD+PD (a mixture of OD and PC)" \| It is OD and PD (Fig. 2 caption, Q_H) \| | \| D2 \| Methods p.13281 \| The honest mixed state is labelled "OD+PD (a mixture of OD and PC)" \| We read it as a mixture of OD and PD (Fig. 2 caption, Q_H) \| | D2: 'called' / 'It is' replaced |
| \| D3 \| Fig. 3 caption \| "8 or 9, respectively" is reversed relative to the figure (the SI, p.1, agrees with the figure) \| | \| D3 \| Fig. 3 caption \| "8 or 9, respectively" lists the states in the opposite order to the panels (the SI, p.1, follows the panels) \| | D3: 'is reversed relative to the figure' replaced |
| \| D4 \| Transition matrix T \| Row 3 omits allOD (H) -> allOD (C), although the SI text (p.2) says corrupt umpires invade this state \| State 3 is transient; stationary distribution unchanged (symbolic check). Confirmed by the SI \| | \| D4 \| Transition matrix T \| Row 3 has no entry for allOD (H) -> allOD (C), while the SI text (p.2) describes corrupt umpires invading this state \| State 3 is transient, so the stationary distribution is the same with or without the entry (symbolic check) \| | D4: 'omits ... although' replaced |
| \| D5 \| (withdrawn) \| We had called the mu/6 entry in row 4 inconsistent \| The SI (p.2) explains it: a neutral dissident fixes with probability 1/2 when two copies already do better. Our derivation now uses this rule \| | (removed) | D5 row removed (kept only in CHANGES_SI.md and DECISIONS.md) |
| \| D6 \| Fig. 3C, D \| Caption says the orange orbit (mu = nu = 1e-4) is shown; its period is {{PerSlow}} time units \| The panels match the mu = nu = 0.02 orbit | \| D6 \| Fig. 3C, D \| The caption refers to the orange orbit (mu = nu = 1e-4, period {{PerSlow}} time units) \| The values in the panels match the mu = nu = 0.02 orbit, which we use for comparison | D6: neutral phrasing |
| \| D7 \| SI Fig. 9 \| Axis labels swapped relative to the caption \| The caption is right (ranges, Hopf boundary and periods agree with our model) \| | \| D7 \| SI Fig. 9 \| The axis labels of the panels are exchanged relative to the caption \| We follow the caption; the ranges, the Hopf boundary and the periods then agree with our model \| | D7: 'swapped' / 'The caption is right' replaced |
| \| PMC \| Web version \| Minus signs lost \| All signs read from the PDF at 300 dpi and checked symbolically \| | \| PMC \| Web version \| The PMC web version does not display the minus signs of the payoff matrices \| All signs read from the PDF at 300 dpi and checked symbolically \| | PMC: 'Minus signs lost' replaced |

### `docs_src/FINAL_REPORT.md.in`

| Before | After | Note |
|---|---|---|
| ## 2. Every discrepancy found - **D1** Q(y) weighting swapped in the printed Methods (in the PDF itself). Resolved to y Q_H + (1 - y) Q_C; the printed form fails B1 (OC -> {{PrintedOC}} with all umpires corrupt). - **D2** Honest mixed state misnamed "OD+PD (a mixture of OD and PC)"; it is OD and PD. - **D3** Fig. 3 caption "8 or 9, respectively" reversed relative to the figure; explained by the | ## 2. Notation inconsistencies and other reproduction notes The reproduction relies on the clear and detailed description by Lee et al. (2019). In a few places the text can be read in more than one way; none of these affects their conclusions. - **D1** The printed Methods weight Q(y) as y Q_C + (1 - y) Q_H, while y is the honest fraction. We read it as y Q_H + (1 - y) Q_C, which gives the stated B ... | section 2 heading and D1-D3 wording ('swapped', 'misnamed', 'reversed', 'fails') |
| - **D4** Printed T omits allOD(H) -> allOD(C); transient row, no effect. The SI text (p.2) states that corrupt umpires invade this state, so the omission is confirmed. - **D5 (withdrawn)** We had flagged the mu/6 entry in row 4. The SI (p.2) gives the rule behind it: a neutral player mutant fixes with probability 1/2 if two mutants do better. Our derivation now uses the SI rules and reproduces the ... | - **D4** The printed T has no entry for allOD(H) -> allOD(C), while the SI text (p.2) describes corrupt umpires invading this state. The row is transient, so the stationary distribution is the same either way. Our derivation uses the SI's fixation rules and reproduces the printed T in every other entry. | D4 wording ('omits', 'omission is confirmed'); D5 bullet removed |
| - **D7 (new, from the SI)** SI Fig. 9 axis labels are swapped relative to its caption; the caption is right. | - **D7 (from the SI)** In SI Fig. 9 the axis labels of the panels are exchanged relative to the caption; we follow the caption. | D7 wording ('swapped', 'the caption is right') |
| - **PMC** web version lost minus signs; all signs taken from the PDF. | - **PMC** The web version does not display the minus signs of the payoff matrices; all signs were taken from the PDF. | PMC wording ('lost minus signs') |

### `docs_src/REVIEW.md.in`

| Before | After | Note |
|---|---|---|
| \| Discrepancies with the original paper reported \| Yes: D1-D4, D6, D7 (D5 withdrawn after reading the SI) and U1-U4 (README, paper Appendix B, SPEC.md, SI_EXTRACT.md). \| | \| Notation inconsistencies in the original paper reported neutrally \| Yes: D1-D4, D6, D7 and U1-U4 (README, paper Appendix B, SPEC.md, SI_EXTRACT.md). \| | checklist row; D5 mention removed |
| - Markov chain: the SI fixation rules for neutral mutants explain every printed entry of T except D4. D5 was our error and is withdrawn. The SI's cost-free chain is reproduced exactly. - Fig. 3 caption (D3) and the T omission (D4) are confirmed by the SI text. | - Markov chain: the SI fixation rules for neutral mutants explain every printed entry of T except D4, and they corrected our own first derivation of one entry (CHANGES_SI.md). The SI's cost-free chain is reproduced exactly. - The SI text supports our readings of the Fig. 3 caption (D3) and of row 3 of T (D4). | SI section: 'D5 was our error' removed; 'T omission ... confirmed' replaced |
| - New inconsistency D7: SI Fig. 9 axis labels are swapped relative to its caption. | - New notation inconsistency D7: in SI Fig. 9 the axis labels are exchanged relative to the caption. | D7 wording ('swapped') |

### `docs_src/CHANGES_SI.md.in`

| Before | After | Note |
|---|---|---|
| - **Discrepancy D5 was withdrawn** (our misreading). D1, D2, D3, D4 and D6 were confirmed; a new inconsistency D7 (SI Fig. 9 axis labels) was found. | - **Item D5 was withdrawn: it was our misreading**, not an inconsistency in the original. The SI supports our readings of D1, D2, D3, D4 and D6, and one further notation inconsistency, D7 (SI Fig. 9 axis labels), was noted. | summary: D5 described as our misreading; 'confirmed' replaced |
| ## 4. Discrepancies D1 to D7 | ## 4. Notation inconsistencies D1 to D7 | heading |
| \| D2 OD+PD called "OD and PC" \| confirmed \| SI p.1 derives the OD-PD fixed point; SI p.2 repeats the slip \| | \| D2 OD+PD labelled "OD and PC" \| reading supported \| SI p.1 derives the OD-PD fixed point; SI p.2 uses the same label \| | D2 row ('called', 'slip') |
| \| D5 mu/6 vs 0 for neutral mutants \| **withdrawn** \| SI p.2 explains both entries (two-mutant rule) \| | \| D5 mu/6 vs 0 for neutral mutants \| **withdrawn: our misreading** \| SI p.2 explains both entries (two-mutant rule); the printed entries are consistent \| | D5 row: described as our misreading |
| \| D7 SI Fig. 9 axis labels \| **new** \| Caption: h horizontal, mu = nu vertical; panels: swapped labels \| | \| D7 SI Fig. 9 axis labels \| **new** \| Caption: h horizontal, mu = nu vertical; panel labels exchanged \| | D7 row ('swapped') |

### `SPEC.md`

| Before | After | Note |
|---|---|---|
| DISCREPANCY D1 (typo in the PDF itself, not only PMC) | NOTATION INCONSISTENCY D1 (in the PDF itself, not only PMC) | D1 label ('typo') |
| which also shows the printed reading fails B1) | which also shows that the literal reading does not give B1) | D1 ('fails B1') |
| DISCREPANCY D2: | NOTATION INCONSISTENCY D2: | D2 label |
| DISCREPANCY D3 (text vs figure) | NOTATION INCONSISTENCY D3 (text vs figure) | D3 label |
| DISCREPANCY D4 (confirmed): row 3 (allOD, honest) omits the transition to 8 | NOTATION INCONSISTENCY D4 (reading supported by the SI): row 3 (allOD, honest) has no entry for the transition to 8 | D4 ('omits') |
| DISCREPANCY D7: the panel axis labels are swapped relative to the caption | NOTATION INCONSISTENCY D7: the panel axis labels are exchanged relative to the caption | D7 ('swapped') |
| has no entry for the transition to 8, although the SI text says | has no entry for the transition to 8, while the SI text says | D4 wording |
| - D5 WITHDRAWN: the entry m/6 in row 4 is explained by the SI (p.2); the 0 in row 7 (PD into allPC under corrupt umpires) follows from the same rule because two PD players do worse. | - The entry m/6 in row 4 follows from the SI rule above (p.2); the 0 in row 7 (PD into allPC under corrupt umpires) follows from the same rule because two PD players do worse. Our first derivation had missed this rule (CHANGES_SI.md). | D5 label removed; described as our derivation change |

### `SI_EXTRACT.md`

| Before | After | Note |
|---|---|---|
| ## Discrepancies D1 to D6 (and a new D7) | ## Notation inconsistencies D1 to D4, D6 and D7 | heading; D5 removed |
| \| **confirmed** (y1 is the honest fraction; the printed weighting is swapped) \| | \| **reading supported** (y1 is the honest fraction; the printed weighting exchanges Q_H and Q_C) \| | D1 ('swapped') |
| SI p.2 repeats the slip ("OD+PD (the last because of the mutual invasibility of OD and PC)") | SI p.2 uses the same label ("OD+PD (the last because of the mutual invasibility of OD and PC)") | D2 ('repeats the slip') |
| \| **confirmed** (the state mixes OD and PD; the "PC" is a slip repeated in the SI) \| | \| **reading supported** (the state mixes OD and PD; the label "PC" also appears in the SI) \| | D2 verdict ('slip') |
| is reversed relative to the figure \| | lists the states in the opposite order to the panels \| | D3 ('reversed') |
| \| **confirmed** (the SI agrees with the figure and with our numerics; the main-text caption is reversed) \| | \| **reading supported** (the SI agrees with the panels and with our numerics) \| | D3 verdict ('caption is reversed') |
| \| D4 \| Printed T omits allOD(H) -> allOD(C) \| | \| D4 \| Printed T has no entry for allOD(H) -> allOD(C) \| | D4 ('omits') |
| \| **confirmed and strengthened** (internal inconsistency in the SI as well); no effect on the stationary distribution \| | \| **reading supported** (the SI text and its matrix differ in the same way); no effect on the stationary distribution \| | D4 verdict |
| \| D5 \| Row 4 entry mu/6 for a neutral player mutant is inconsistent with the 0 given elsewhere \| SI p.2 explains it: a PC dissident in allPD fixes with probability 1/2 because two PC players already do better; a PD dissident in allPC cannot fix because two PD players do worse \| **withdrawn** (our misreading; the entry is correct and our derivation was incomplete) \| | (removed) | D5 row removed (see CHANGES_SI.md) |
| \| **new inconsistency** (axis labels swapped in SI Fig. 9; the caption is right) \| | \| **new notation inconsistency** (panel axis labels exchanged relative to the caption; we follow the caption) \| | D7 ('swapped', 'the caption is right') |
| - SI p.1 contains a slip: | - SI p.1 contains a small notation inconsistency: | other note ('slip') |
| \| **different (pre-SI code was wrong on this point)**; fixed: | \| **different (our pre-SI derivation was incomplete on this point)**; fixed: | U2 row: about our own code |

### `experiments/digitize_si.py`

| Before | After | Note |
|---|---|---|
| DISCREPANCY D7: the panel labels are swapped) | notation inconsistency D7: the panel labels are exchanged) | module docstring |

### `tests/test_fixed_points.py`

| Before | After | Note |
|---|---|---|
| """With Q(y) = y Q_C + (1-y) Q_H as printed, y = 0 gives Q_H and OC -> 1, contradicting B1.""" | """With Q(y) = y Q_C + (1-y) Q_H read literally, y = 0 gives Q_H and OC -> 1, which is not B1.""" | test docstring ('contradicting') |

### `tests/test_rare_exploration.py`

| Before | After | Note |
|---|---|---|
| """States 3, 4, 5 receive no transitions from recurrent states, so D4, D5 are harmless.""" | """States 3, 4, 5 receive no transitions from recurrent states, so their rows (D4) do not affect the stationary distribution.""" | test docstring (D5 label removed) |

## Files reviewed and left unchanged

- `figures/README.md`, `METRICS.md`, `CITATIONS_TODO.md`, `src/*.py`, `configs/`: no wording about
  the original paper that needed a change.
- Figure captions: all captions are in the two paper sources; the only caption that refers to the
  original (our Fig. 2D, "which match Lee et al.'s Fig. 3C, D") was already neutral.
- The author's project brief: kept as written and not distributed (DECISIONS D-026).
- `DECISIONS.md`, `PROGRESS.md`, `CHANGES_SI.md`: dated logs. Earlier entries keep the wording
  used at the time, so the record stays accurate; D5 is described there as our misreading,
  withdrawn after reading the SI (DECISIONS D-019, CHANGES_SI.md Sections 1 and 4).
- `results/pre_si/`: a snapshot of generated numbers, kept unchanged.
