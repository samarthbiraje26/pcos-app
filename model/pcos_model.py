"""
PCOS Detection Model — XGBoost Implementation
================================================
Implements the two functions required by backend/ml_model.py:

    load_model()              → loads pcos_model.pkl from this directory
    predict(model, input_dict) → returns ("Positive"/"Negative", confidence)

SETUP (one-time):
-----------------
1. Open your Colab notebook and run the cells up to Cell 20 (xgb1 training).
2. Then add this cell at the END of your notebook:

        import pickle, google.colab.files as clf
        with open("pcos_model.pkl", "wb") as f:
            pickle.dump(xgb1, f)
        clf.download("pcos_model.pkl")

3. A download will start automatically.
4. Move the downloaded  pcos_model.pkl  into this folder:
       pcos-app/model/pcos_model.pkl

5. Restart the Flask server.  You should see:
       [ML] ✅ PCOS model loaded successfully — real-mode active.
"""

import os
import pickle
import numpy as np
import pandas as pd

# ── Path to the saved model file ──────────────────────────────────────────────
_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pcos_model.pkl")

# ── Column names in the EXACT order the XGBoost model was trained on ──────────
# (These are X_train.columns after dropping PCOS(Y/N), Sl.No, Patient File No.)
MODEL_COLUMNS = [
    "Age (yrs)",
    "Weight (Kg)",
    "Height(Cm)",
    "BMI",
    "Blood Group",
    "Pulse rate(bpm)",
    "Cycle(R/I)",
    "Cycle length(days)",
    "Marraige Status (Yrs)",
    "Pregnant(Y/N)",
    "No. of aborptions",
    "I   beta-HCG(mIU/mL)",
    "II    beta-HCG(mIU/mL)",
    "FSH(mIU/mL)",
    "LH(mIU/mL)",
    "FSH/LH",
    "Hip(inch)",
    "Waist(inch)",
    "Waist:Hip Ratio",
    "TSH (mIU/L)",
    "AMH(ng/mL)",
    "PRL(ng/mL)",
    "Vit D3 (ng/mL)",
    "PRG(ng/mL)",
    "RBS(mg/dl)",
    "Weight gain(Y/N)",
    "hair growth(Y/N)",
    "Skin darkening (Y/N)",
    "Hair loss(Y/N)",
    "Pimples(Y/N)",
    "Fast food (Y/N)",
    "Reg.Exercise(Y/N)",
    "BP _Systolic (mmHg)",
    "BP _Diastolic (mmHg)",
    "Follicle No. (L)",
    "Follicle No. (R)",
    "Avg. F size (L) (mm)",
    "Avg. F size (R) (mm)",
    "Endometrium (mm)",
]

# ── Median fallback values (computed from the PCOS dataset training split) ────
# These are used for columns not collected from the user in the frontend form.
# Values are approximate medians from the public PCOS Kaggle dataset.
MEDIAN_DEFAULTS = {
    "Age (yrs)":               28.0,
    "Weight (Kg)":             60.0,
    "Height(Cm)":             160.0,
    "BMI":                     23.5,
    "Blood Group":             11.0,
    "Pulse rate(bpm)":         78.0,
    "Cycle(R/I)":               2.0,
    "Cycle length(days)":      28.0,
    "Marraige Status (Yrs)":    3.0,
    "Pregnant(Y/N)":            0.0,
    "No. of aborptions":        0.0,
    "I   beta-HCG(mIU/mL)":   13.7,
    "II    beta-HCG(mIU/mL)": 13.0,
    "FSH(mIU/mL)":              6.4,
    "LH(mIU/mL)":               6.4,
    "FSH/LH":                   1.0,
    "Hip(inch)":               38.0,
    "Waist(inch)":             31.0,
    "Waist:Hip Ratio":          0.82,
    "TSH (mIU/L)":              2.1,
    "AMH(ng/mL)":               3.5,
    "PRL(ng/mL)":              16.0,
    "Vit D3 (ng/mL)":          20.0,
    "PRG(ng/mL)":               0.5,
    "RBS(mg/dl)":              88.0,
    "Weight gain(Y/N)":         0.0,
    "hair growth(Y/N)":         0.0,
    "Skin darkening (Y/N)":     0.0,
    "Hair loss(Y/N)":           0.0,
    "Pimples(Y/N)":             0.0,
    "Fast food (Y/N)":          0.0,
    "Reg.Exercise(Y/N)":        0.0,
    "BP _Systolic (mmHg)":    110.0,
    "BP _Diastolic (mmHg)":    70.0,
    "Follicle No. (L)":         5.0,
    "Follicle No. (R)":         5.0,
    "Avg. F size (L) (mm)":    14.0,
    "Avg. F size (R) (mm)":    14.0,
    "Endometrium (mm)":         8.0,
}

# ── Mapping: frontend field name → model column name ─────────────────────────
FIELD_MAP = {
    "age":             "Age (yrs)",
    "weight":          "Weight (Kg)",
    "height":          "Height(Cm)",
    "bmi":             "BMI",
    "blood_group":     "Blood Group",
    "pulse_rate":      "Pulse rate(bpm)",
    "cycle_type":      "Cycle(R/I)",
    "cycle_length":    "Cycle length(days)",
    "marriage_years":  "Marraige Status (Yrs)",
    "pregnant":        "Pregnant(Y/N)",
    "vitamin_d3":      "Vit D3 (ng/mL)",
    "weight_gain":     "Weight gain(Y/N)",
    "hair_growth":     "hair growth(Y/N)",
    "skin_darkening":  "Skin darkening (Y/N)",
    "hair_loss":       "Hair loss(Y/N)",
    "pimples":         "Pimples(Y/N)",
    "fast_food":       "Fast food (Y/N)",
    "reg_exercise":    "Reg.Exercise(Y/N)",
    "follicle_left":   "Follicle No. (L)",
    "follicle_right":  "Follicle No. (R)",
    "avg_fsize_left":  "Avg. F size (L) (mm)",
    "avg_fsize_right": "Avg. F size (R) (mm)",
}


# ── 1. load_model ─────────────────────────────────────────────────────────────

def load_model():
    """
    Load the trained XGBoost model from pcos_model.pkl.
    Called once at server startup by backend/ml_model.py.
    """
    if not os.path.exists(_MODEL_PATH):
        raise FileNotFoundError(
            f"Model file not found: {_MODEL_PATH}\n"
            "Please save your trained model from Colab (see instructions at the top of this file)."
        )

    with open(_MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    print(f"[pcos_model] Loaded model from {_MODEL_PATH}")
    return model


# ── 2. predict ────────────────────────────────────────────────────────────────

def predict(model, input_dict: dict):
    """
    Run PCOS prediction.

    Args:
        model      : Loaded XGBClassifier object (from load_model)
        input_dict : Dict of 22 frontend field values (keys defined in FIELD_MAP)

    Returns:
        Tuple[str, float] : ("Positive" | "Negative", confidence 0–1)
    """
    # Start with median defaults for every column
    row = dict(MEDIAN_DEFAULTS)

    # Overwrite with user-supplied values using the field map
    for frontend_key, model_col in FIELD_MAP.items():
        if frontend_key in input_dict and input_dict[frontend_key] is not None:
            row[model_col] = float(input_dict[frontend_key])

    # Build DataFrame in the exact column order the model was trained on
    # Use model.feature_names_in_ if available, else fall back to MODEL_COLUMNS
    try:
        columns = list(model.feature_names_in_)
    except AttributeError:
        columns = MODEL_COLUMNS

    input_df = pd.DataFrame([row], columns=columns)

    # Predict probability of PCOS (class 1)
    prob_positive = float(model.predict_proba(input_df)[0][1])

    label = "Positive" if prob_positive >= 0.5 else "Negative"
    return label, prob_positive
