# M5 Course Project — Milestones 1 and 2

**Group 2 - MIA5130A Systems Optimization and Management**

- [Milestone 1 — Data Exploration and Understanding](M5_Milestone_1_Data_Exploration_and_Understanding.ipynb): data exploration,
  illustrative baselines, and the report-ready Data Understanding draft.
- [Milestone 2 — Demand Forecasting](M5_Milestone_2_Demand_Forecasting.ipynb): the fixed CA_1 experiment, product
  selection audit, weekly features, trained models, held-out evaluation, prediction intervals, and forecast plots.

Both notebooks include their own setup and can run independently from a fresh
kernel. Run the notebook you need from top to bottom; Milestone 2 reads the raw
CSV files directly and does not depend on Milestone 1 outputs or kernel state.

## Setup

Use Python 3.15 with the NumPy and pandas versions pinned in `requirements.txt`. In a terminal
opened in this project folder:

```bash
python3.15 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m ipykernel install --user --name m5-exploration --display-name "Python 3.15 (M5 exploration)"
jupyter lab
```

Select **Python 3.15 (M5 exploration)** when opening either notebook. In VS Code,
select this kernel or the project's `.venv/bin/python` interpreter. After updating
packages, restart the kernel and run the selected notebook from top to bottom. A kernel
restart clears imports, so running a later cell first can produce `pd is not defined`.

The pinned versions replace older native NumPy/pandas builds that crashed during
date conversion on Python 3.15. Each setup cell checks compatibility before loading
those extensions. Calendar dates are explicitly parsed as ISO dates and normalized
to nanosecond resolution for consistent joins and CSV round-trips.

## Data location

Obtain the data from [Kaggle](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data).
Place the five CSV files in `data/`, or set `DATA_DIR_OVERRIDE` in the first code cell.
Both notebooks also find `~/Downloads/m5-forecasting-accuracy` automatically.
Alternatively set `M5_DATA_DIR` to that folder before opening Jupyter.

Milestone 1 uses all five files:

- calendar.csv
- sales_train_evaluation.csv
- sales_train_validation.csv
- sell_prices.csv
- sample_submission.csv

Milestone 2 requires only `calendar.csv`, `sales_train_evaluation.csv`, and
`sell_prices.csv`.

Raw CSV files are read in place; they are not copied into this project or modified.
The full audit uses the wide sales matrix; only ten selected product-store series
are converted to long format. Allow approximately 1–2 GB of available working memory.

## Milestone 1 contents

- File inventory, checksums, schemas, and data dictionary.
- Full overlap verification between the two sales files.
- Keys, nulls, values, dates, hierarchy, and complete historical price-join audit.
- Sales distributions, trends, seasonality, events, SNAP, and price exploration.
- An illustrative ten-product subset selected with training-period data only.
- Weekly target and inputs, chronological splits, and independent timing checks.
- Rolling-origin validation baselines; the final test window is not scored.
- Inventory and routing limitations and a generated Data Understanding draft.

## Milestone 2 contents

Start with the notebook's unnumbered setup, then follow its five clearly separated sections:

| Section | Completed work |
|---|---|
| **1. Set the experiment** | Ten CA_1 products, weekly target, chronological splits, and selection audit |
| **2. Prepare the final dataset** | Historical sales/price features, calendar inputs, and independent leakage checks |
| **3. Train and compare models** | Seasonal-naive, four-week-average, polynomial, and ridge models; chronological tuning and validation selection |
| **4. Evaluate forecasts** | MAE/RMSE/WAPE on 560 common test observations; product/quarter comparisons and the 10% target assessment |
| **5. Add uncertainty and plots** | Saved 80%/95% calibration applied to all test forecasts; coverage and widths; actual-versus-predicted plots for all ten products and four models |

**All five technical sections are implemented.** The separate Milestone 2 submission
write-up remains to be assembled. See the [validation comparison](outputs/milestone2/models/README.md),
[point-forecast test evaluation](outputs/milestone2/evaluation/README.md), and
[prediction intervals and coverage](outputs/milestone2/uncertainty/README.md) for results and limitations.

The test analysis retains the original fitted models, validation-selected ridge, and
interval calibration saved before the first test evaluation. Test outcomes do not drive
tuning, refitting, model selection, or interval calibration. Observed coverage is reported
without claiming exact coverage guarantees for dependent time-series data.

## Outputs

Milestone 1 writes directly under `outputs/`: eight figure PNGs, compact profile/quality tables, the selected
daily sales table, a weekly forecasting panel, `data_profile.json`, exact runtime
versions, and `data_understanding.md`. These describe the earlier exploratory experiment.

Milestone 2 writes its final dataset and supporting tables under `outputs/milestone2/`.
See [the dataset handoff](outputs/milestone2/README.md) for predictor definitions
and timing assumptions. Model outputs, figures, fitted parameters, and the validation
comparison are in `outputs/milestone2/models/`. Final test forecasts, metric tables,
target assessments, figures, frozen settings, and checks are in
`outputs/milestone2/evaluation/`. Interval forecasts, coverage and width tables,
uncertainty figures, and checks are in `outputs/milestone2/uncertainty/`.
`outputs/milestone2/notebook_validation.json`
records the fresh-kernel execution and checks. Running either notebook regenerates
its analytical outputs; the validation record documents the verified saved copy.
The raw dataset remains the source of truth; exported subsets are analysis products.

Milestone 1 preserves the original exploratory scope; Milestone 2 contains the
fixed ten-product experiment, trained models, validation/test comparisons,
prediction intervals, and coverage analysis.
Inventory and routing optimization remain later milestones.
M5 describes U.S. retail activity: SNAP is defined in the notebook, and prices are in USD.
