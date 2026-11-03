# AI Prediction: Dataset, Features, Evaluation, Limitations

## Data provenance
Generated with `train_model.py` using a seeded thermal simulation (`SEED=20261021`). Every trajectory varies initial temperature, ambient temperature, insulation rate, refrigeration strength, door-opening event, power interruption timing, and compressor efficiency. These are synthetic engineering assumptions, not traces from vaccines, clinics, or actual ESP32s. Code and seed permit reproduction.

**Dataset split:** 220 independently seeded trajectories, 171 train and 49 test trajectories; 9,405 training windows and 2,695 held-out windows. Split by whole trajectory with `GroupShuffleSplit`, not by individual correlated windows. Each feature input is a 6-minute observation window sampled once per minute. Prediction target = the physical state in the same synthetic trajectory 30 minutes later. Deployed telemetry aggregates last ~5 minutes of 5-second device messages into equivalent features.

## Features
1. `temp_c`: last reading in °C.
2. `slope_c_per_min`: linear first-last temperature trend in °C per minute (clipped).
3. `mean_c`: observed temperature mean.
4. `std_c`: observed temperature variation.
5. `door_open`: most recent door switch status.
6. `mains_ok`: most recent mains/power status.
7. `compressor_on`: most recent motor status.
8. `compressor_duty`: fraction of recent observations with motor energized.

## Model
Scikit-learn `RandomForestRegressor` with 30 trees, maximum depth 10, minimum leaf size 10 (smaller and slightly more accurate than the earlier 75-tree model; loads quickly on a small server), `random_state=20261021`. No future samples enter the features. Alert when the predicted temperature **exceeds 8°C**; model is advisory.

## Holdout results (synthetic-only)
See source file `report/model_metrics.json` and figure `report/forecast_validation.png`. Values come from executing the training script, not estimates:

- Test MAE: **1.478°C**.
- Test RMSE: **1.873°C**.
- Forecast breach classification (`>8°C`): precision **0.866**, recall **0.870**, F1 **0.868**.
- Confusion matrix: TN **1110**, FP **188**, FN **181**, TP **1216**.

## Required next validation
- Acquire at least several actual fridge temperature traces with ground-truth calibrated sensors, door, power and compressor operation, with storage-unit/device holdout.
- Assess forecast MAE near the 8°C safety boundary, missed-breach rate, calibration, lead time, cold-start and uncommon equipment failures.
- Calibrate cooling health by fridge type, fill state and ambient conditions. Do not equate the current score to remaining useful life.
- Define hospital/pharmacy SOPs for relocation (physical verification, refrigerator capacity, quarantine and clinician approval).
- Report test performance only after prospective site validation; the synthetic scores cannot be generalized to medical cold chains.
