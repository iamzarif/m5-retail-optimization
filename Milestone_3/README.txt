MIA 5130 — Milestone 3 supporting materials

Run:
python Milestone3_Reproduce.py --data-dir /path/to/data --output-dir ./Milestone3_Support

Method: exact Milestone 2 ridge model (fitted through 2015-03-01; alpha 100)
reproduces test MAE 25.11791598 and RMSE 36.51215471,
then predicts 2016-05-23 to 2016-05-29 using as-of 2016-05-22 inputs.
Scenario 1 minimizes proportional integer rounding deviation using largest remainders.
Scenario 2 maximizes selling-price revenue with allocation bounds
floor(0.80*quota) <= allocation <= ceil(1.20*quota),
subject to 100 units, integrality, and forecast-demand caps.
An analytical descending-price fill is optimal under these conditions.

All figures refer to potential sales revenue, not cost-adjusted profit.
The 20% bound is a clearly disclosed case-study choice.

Files:
m3_forecast_handoff.csv - dated forecast and price provenance
m3_scenario1_proportional.csv - Scenario 1 allocations and conditional revenues
m3_scenario2_bounded_revenue_optimal.csv - Scenario 2 bounds and optimal allocations
m3_analytical_solution_steps.csv - transparent stepwise marginal allocations
m3_original_vs_reproduced_audit.csv - differences from the undated original files
m3_summary_reproduced.json - consolidated results and numerical checks
m3_analytical_method_evidence.png - figure with the actual solution worksheet
m3_scenario_revenue_comparison.png - comparison chart

The small m3_selected_price_history.csv file is a 10-item CA_1
extract of the supplied sell_prices.csv through May 20, 2016.
It permits reproducibility without distributing the full 194 MB price file.
