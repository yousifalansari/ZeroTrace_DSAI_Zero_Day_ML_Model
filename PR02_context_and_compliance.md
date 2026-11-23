# Progress Report 02 context and compliance record

This file preserves the verified project context used to prepare `Progress_Report_02.docx` and `Progress_Report_02.pdf`. It is intended to support later report revisions without repeating the audit or changing the research question.

## Repository cleanup and dataset access

At the team's request, these three large raw corpus files were removed from the working tree because each exceeded 100 MB: `UNSW-NB15_DATA/UNSW-NB15_1.csv` (161.15 MiB), `UNSW-NB15_DATA/UNSW-NB15_2.csv` (157.57 MiB), and `UNSW-NB15_DATA/UNSW-NB15_3.csv` (147.43 MiB). They are not direct inputs to the report's experiment runner. README.md includes placeholders for their source links; fill those in before publishing if the team wants others to download the raw parts.

To reproduce the reported experiments, the required files are the smaller official partitions `data/train.csv` (175,341 rows) and `data/test.csv` (82,332 rows). If they need to be restored, download the compatible training and testing partitions from the official source or an approved mirror (the links are intentionally marked for insertion in README.md), then place them in `data/` with those exact filenames. Do not substitute the three raw corpus parts for these partitions. `UNSW-NB15_DATA/` still contains the dataset description, feature notes, ground-truth and event files, `UNSW-NB15_4.csv`, and copies of the named train/test partitions.

The repository guide, README.md, now describes the project files, experiment workflow, dataset setup, report outputs, and known interpretation limits in one place. `.gitignore` excludes Python cache files and the three removed raw CSV paths so they are not accidentally added again.

## Authority and report structure

The official project guidelines and Progress Report 02 rubric in `project resources/DSAI310_Fall2026_Project(1).pdf` are authoritative. The original proposal and `project resources/Progress Report 01 Machine Learning for Detecting Previously (1).pdf` establish the project question, terminology, planned model comparison, and IEEE-style numbered references.

The report retains the Progress Report 01 main-section order:

1. Introduction
2. Related Work
3. Dataset
4. Methodology
5. Experiments
6. Results and Analysis
7. Contributions
8. Conclusion
9. References

Progress Report 02 rubric content is included in the matching sections as labeled subsections: dataset exploration and data quality; data preparation and feature creation; methods and modeling; tool-based data and modeling workflow; initial experiments and results; reproducible implementation and data access.

## Requirement checklist

| Official requirement | Status | Evidence / remaining work |
|---|---|---|
| Same main sections and order as Progress Report 01 | Satisfied | All nine sections retained in order. |
| Dataset described with statistics and visualizations | Satisfied | Partition/category counts, selected numeric summaries, label/category plot, and selected feature distributions included. |
| Missing values, duplicates, outliers, labels, and imbalance investigated | Satisfied | Quality table and discussion document zero missing cells and label disagreement, duplicate counts, retained outliers, class proportions, and rare categories. |
| Explain implications of quality findings | Satisfied | Class weighting, per-category recall, uncertainty intervals, training-only duplicate/conflict filtering, and exact-vector-overlap limitations are explained. |
| Data preparation and feature creation documented | Satisfied | Cleaning, feature engineering, correlation pruning, categorical encoding, skew transforms, scaling, and fold-local fitting are described. |
| Appropriate training/test separation and preprocessing fitted using training data only | Satisfied | Official partitions are verified; all model preprocessing/selection is pipelined and fitted within training CV folds; test data is not used to fit transformations or tune. |
| Implement baseline and describe planned/compared configurations | Satisfied | LR baseline plus proposal models RF and XGBoost; parameter grids, weights, three-fold CV and threshold are documented. |
| Initial evaluation metrics, analysis, and interpretation | Satisfied | E1 metrics, E2 per-category recall/FPR and intervals, feature-unseen sensitivity, generalization gap, and critical discussion are included. |
| Executable, organized code showing data loading, cleaning, features, visualization, training, and evaluation | Satisfied | `run_pr02.py`, `generate_pr02_color_figures.py`, and retained notebook. |
| Dataset or clear access/reproduction instructions | Satisfied | Dataset is bundled under `data/`; README gives source and row-count identification; report gives run command, dependencies, seed, and output paths. |
| Reproducible results and verifiable figures | Satisfied | Run manifest stores dataset hashes, versions, row counts, seeds and CV folds; outputs are generated from the runner and tables. |
| Contributions for this reporting period | Partially satisfied | PR01 planned assignments are preserved, but no PR02 task log or meeting history exists. The team must fill in actual PR02 tasks from its own records. |
| Full feature-importance explanation and feature-distribution analysis of misses | Not required for PR02 initial-results rubric; still outstanding from the proposal analysis plan | Missed records and probabilities are exported for follow-up. Report does not claim causal explanations. |

The report does not claim full completion of all research objectives because PR02 contribution evidence and deeper feature-importance/error-cause analyses are not available. A course grade cannot be guaranteed; the checklist maps the visible deliverable to the supplied rubric.

## Verified dataset and version choice

- Modeling files: `data/train.csv` (175,341 x 45) and `data/test.csv` (82,332 x 45).
- Use the author-provided partition CSVs reflected in those files and recorded by SHA-256 in `results/pr02/run_manifest.json`.
- Each partition has an identifier, 42 flow fields, `attack_cat`, and binary `label`.
- `label` is the prediction target. `attack_cat` is used only to create category holdouts and report grouped results. `id` is not an input.
- Expected category counts are checked by the runner. Files are assigned by row count to avoid reversing upstream filename conventions.
- The report describes the official author partition files as its source. It does not silently substitute a Google Sheets or Kaggle mirror version.
- Quality check: zero missing cells, zero negative numeric values, and zero label/category disagreements. Exact duplicate rows ignoring `id`: 67,601 in train and 26,387 in test. Train-only duplicate removal leaves 107,740 rows; removing 458 conflicting-label rows leaves 107,282. Test is not cleaned.
- Train is 68.1% attack; test is 55.1% attack. Worms has only 44 test rows.
- Outliers are statistical IQR flags and are retained; eligible skewed numeric features receive log1p and scaling within folds.

## Verified implementation and experiments

- `PR02_UNSW_NB15_workflow.ipynb` preserves EDA and the Logistic Regression exploratory workflow only. Its stored E2 Fuzzers preview is 0.487 (rounded). The report’s completed three-model comparison is generated separately by `run_pr02.py`; its seed-42 LR E2 Fuzzers result is 0.488783, rounded to 0.489. The current project files do not verify the alternative 0.494 value. These are distinct workflows and the report names their sources explicitly.
- E1: fit on the cleaned official training partition; evaluate on all official test records.
- E2: repeat for each of the nine attack categories after excluding that category from training; evaluate on test normal records and test records from the excluded category.
- Models: Logistic Regression (balanced class weights; C in {0.1, 1, 10}), Random Forest (balanced subsampling; 100 trees; depth None or 18), XGBoost (150 trees, depth 4 or 6, learning rate 0.08, histogram method, positive class weighting).
- Three-fold stratified CV scored by F1; fixed probability threshold 0.5; test data is reserved for final evaluation. The runner, rather than the LR-only notebook, is the canonical source of the report’s LR/RF/XGBoost tables.
- Primary seed 42; repeats 7 and 21. Wilson 95% intervals are reported for category recall.
- Feature preparation: four flow-derived features, drop redundant `is_ftp_login`, fold-local correlation pruning at 0.95, log transforms based on training-fold skew, standard scaling, one-hot encoding for `proto`, `service`, and `state`, with infrequent/unknown handling.
- Exact feature-vector overlap is computed ignoring `id`, category, and label. E2 recall is also reported after excluding held-out vectors present in the remaining training data. This is an exact-match sensitivity subset, not proof of semantic novelty.
- Individual E2 false negatives and predicted attack probabilities are exported in `results/pr02/E2_missed_attack_records.csv`.

## Verified primary E1 results (seed 42)

| Model | Accuracy | Precision | Recall | F1 | FPR | ROC-AUC | Average precision |
|---|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.8383 | 0.7817 | 0.9802 | 0.8697 | 0.3355 | 0.9654 | 0.9721 |
| Random Forest | 0.8703 | 0.8167 | 0.9858 | 0.8933 | 0.2712 | 0.9785 | 0.9812 |
| XGBoost | 0.8805 | 0.8293 | 0.9859 | 0.9009 | 0.2486 | 0.9853 | 0.9891 |

Fuzzers was the weakest held-out category for each model: LR 0.4888 recall, RF 0.4654, XGBoost 0.4170. Mean strict feature-unseen recall across the nine category holdouts was LR 0.9009, RF 0.9293, XGBoost 0.9242. Each model's mean exact-vector overlap fraction across category holdouts was 10.7%. The complete per-category results are in `results/pr02/E2_loaco.csv`; seed results are in `results/pr02/seed_sensitivity.csv`.

## Remaining limitations

These limitations and their implications are discussed in Section 6.5 of the report. The final-report iteration should:

- Extend the seed check to at least ten prespecified seeds and report between-run variation separately from per-test-record Wilson intervals.
- Add a documented near-duplicate sensitivity analysis while preserving exact-vector filtering as the reference result.
- Choose candidate alert thresholds using training-only validation, then report threshold curves and prevalence-sensitive alert measures on the untouched official test partition.
- Retain absolute TP/FN counts and intervals for rare categories; seek independent samples only if a compatible, documented source is available.
- Add temporal or environment-separated evaluation only if defensible metadata or an independent dataset supports it; otherwise keep the category-holdout scope explicit.
- Compare missed, detected, and normal records by category and report feature importance only as a predictive association, not a causal explanation.
- Obtain team-confirmed PR02 contributions before submission.
- Describe results as benchmark category-holdout evidence, never as operational zero-day protection.

## Reproduction

From the project root, install `requirements.txt`, ensure the dataset files are present, and run:

```bash
python run_pr02.py --data-dir data --include-xgboost --repeat-seeds
python generate_pr02_color_figures.py
python build_pr02_report.py
```

On macOS, XGBoost may require `brew install libomp`. The editable report is `Progress_Report_02.docx`; the searchable, text-based submission PDF is `Progress_Report_02.pdf`.
