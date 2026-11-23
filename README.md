# Zero-Day Attack Detection with Machine Learning

This repository contains our DSAI 310 project on detecting network attacks with supervised machine learning. The work uses the UNSW-NB15 benchmark and asks a focused question: how well do binary attack classifiers perform when an attack category is left out of training? The experiments are a benchmark study. They do not establish that a model can protect a live network from operational zero-day attacks.

The project grew over several stages. The notebook records the original data exploration and Logistic Regression baseline. The PR02 source runner adds a repeatable comparison of Logistic Regression, Random Forest, and XGBoost, with a conventional test and nine label-based category holdouts. The report uses the runner's saved results for that three-model comparison.

## Dataset files

The experiment runner expects the official training and test partitions in `data/`:

| File | Rows | Columns | SHA-256 |
|---|---:|---:|---|
| `data/train.csv` | 175,341 | 45 | `bec7dd5ec88dc2a0ccc7a07879d338395ed7421750f675fd0339e07dfe0648fa` |
| `data/test.csv` | 82,332 | 45 | `734fe6642edf758f7c94d7d9149426b49d202fe8e7bf0bef47392489c3c0a559` |

To replace or restore the dataset, download the official UNSW-NB15 files from **[insert official download link here]**. A mirror is available at **[insert mirror link here]**. Download and extract the files, then put the compatible training and test partition CSVs in `data/`, named exactly `train.csv` and `test.csv`. Use the 175,341-row partition as `train.csv` and the 82,332-row partition as `test.csv`; some source archives use confusing filenames, so check row counts rather than relying on filenames. The runner checks the partition dimensions and category counts before training. The SHA-256 values above identify the versions used for the reported results.

Three large raw corpus files were removed from the working tree to keep the repository smaller:

- `UNSW-NB15_DATA/UNSW-NB15_1.csv` (about 161 MB) — [https://unsw-my.sharepoint.com/:x:/r/personal/z5025758_ad_unsw_edu_au/_layouts/15/Doc.aspx?sourcedoc=%7B4C4B6D3A-D264-487B-B677-DFAC2175F783%7D&file=UNSW-NB15_1.csv&action=default&mobileredirect=true]
- `UNSW-NB15_DATA/UNSW-NB15_2.csv` (about 158 MB) — [https://unsw-my.sharepoint.com/:x:/r/personal/z5025758_ad_unsw_edu_au/_layouts/15/Doc.aspx?sourcedoc=%7BCB831326-E652-459D-8033-F773D42F60EC%7D&file=UNSW-NB15_2.csv&action=default&mobileredirect=true]
- `UNSW-NB15_DATA/UNSW-NB15_3.csv` (about 147 MB) — [https://unsw-my.sharepoint.com/:x:/r/personal/z5025758_ad_unsw_edu_au/_layouts/15/Doc.aspx?sourcedoc=%7B1DD6A5D4-AB33-4FE6-838F-FE16125F744F%7D&file=UNSW-NB15_3.csv&action=default&mobileredirect=true]

These are raw corpus parts, not the two partition files used by the reported experiments. They are not needed to reproduce the report if `data/train.csv` and `data/test.csv` are present. If you need the raw parts for separate analysis, download them from the source links above and place them in `UNSW-NB15_DATA/`; do not use them in place of the required files under `data/`.

## Setup and reproduction

From the repository root, create an environment and install the Python packages:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

To reproduce the report's full three-model run, use:

```bash
python run_pr02.py --data-dir data --include-xgboost --repeat-seeds
python generate_pr02_color_figures.py
python build_pr02_report.py
```

On macOS, XGBoost may also need the OpenMP runtime: `brew install libomp`. The runner uses seed 42 for the primary results and repeats the experiments with seeds 7 and 21. It performs three-fold stratified cross-validation, keeps the test threshold at 0.5, and writes metrics, data checks, and a run manifest to `results/pr02/`. The manifest records dataset hashes, software versions, row counts, model names, and settings.

The notebook is still useful for reading the exploratory work and the initial Logistic Regression workflow. It does not contain the Random Forest and XGBoost experiment cells; those report results come from `run_pr02.py`. The notebook's saved Fuzzers holdout preview for Logistic Regression is 0.487. The runner's corresponding seed-42 result is 0.488783, rounded to 0.489. These values come from distinct workflows and are documented separately; the current project files do not verify a 0.494 result.

## What's in the repository

- `PR02_UNSW_NB15_workflow.ipynb` — exploratory analysis, data-quality work, and the initial Logistic Regression experiments, with saved outputs.
- `run_pr02.py` — the reproducible runner for the reported Logistic Regression, Random Forest, and XGBoost comparison.
- `generate_pr02_color_figures.py` — regenerates the color figures used in the report.
- `generate_pr02_bw_figures.py` — regenerates black-and-white versions of the PR02 figures.
- `build_pr02_report.py` — builds the editable Word report from the saved experiment results and figures.
- `Progress_Report_02.docx` and `Progress_Report_02.pdf` — editable and submission-ready report files.
- `PR02_context_and_compliance.md` — the detailed project record: requirements checklist, data decisions, verified results, limitations, and reproduction notes.
- `project resources/` — the official course project guidelines, original proposal, and Progress Report 01 used to guide PR02.
- `data/` — the exact train/test partitions required by the runner.
- `UNSW-NB15_DATA/` — supporting dataset documentation and smaller source files retained in the project; the three raw parts listed above were removed.
- `figures/` — figures from the original notebook and generated PR02 figures. The `pr02/` subfolder contains color and monochrome variants.
- `results/` — saved notebook results and PR02 machine-readable outputs. `results/pr02/E1_overall.csv` and `E2_loaco.csv` are the main result tables; `run_manifest.json` records the run configuration, and the false-negative file supports further error review.
- `requirements.txt` — Python dependencies used by the workflow.

## How to read the results

E1 is the conventional reference experiment, in which all attack categories appear in training. E2 leaves one attack category out of training and evaluates that category alongside normal test traffic. Results include attack recall and false-positive rate because recall by itself does not show the alert burden. The exact-vector sensitivity analysis removes held-out records whose feature vectors match records in the remaining training data; it does not identify near-duplicates or prove that an attack is genuinely novel.

The course report discusses the high false-positive rates, differences between the official partitions, small category counts (including 44 Worms test records), the limited three-seed sensitivity check, and the limits of label-based holdouts. The results should be described as category-holdout benchmark evidence, not as proof of operational zero-day protection. PR02 contribution entries still need confirmation from the team before submission.
