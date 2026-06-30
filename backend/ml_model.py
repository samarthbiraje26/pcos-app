"""
PCOS Detection ML Model Wrapper
================================
This module wraps the XGBoost model for PCOS detection.

HOW TO INTEGRATE YOUR MODEL
----------------------------
1. Place your trained model file (e.g., model.pkl / model.json) inside the /model/ directory.
2. Edit  model/pcos_model.py  and implement:
      load_model()  -> returns the loaded model object
      predict(model, input_dict) -> returns (result_str, confidence_float)
         result_str     : "Positive" or "Negative"
         confidence_float: float between 0 and 1

3. Once pcos_model.py is implemented, the wrapper below will automatically detect it
   and switch from mock-mode to real-model mode on the next server restart.

CURRENT STATE
-------------
mock-mode is ACTIVE — heuristic rules are used until the real model is provided.
"""

import os
import sys

# Add /model/ directory to Python path
MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model"
)
sys.path.insert(0, MODEL_DIR)


class PCOSModel:
    """
    Singleton wrapper around the XGBoost PCOS detection model.
    Falls back to deterministic heuristic predictions when the real model is absent.
    """

    def __init__(self):
        self.model     = None
        self.is_loaded = False
        self._load_model()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _load_model(self):
        """Try to import and load the user-supplied model."""
        try:
            import pcos_model                           # model/pcos_model.py
            self.model     = pcos_model.load_model()
            self.is_loaded = True
            print("[ML] ✅ PCOS model loaded successfully — real-mode active.")
        except Exception as exc:
            print(f"[ML] ⚠️  Model not available ({exc}) — mock-mode active.")
            self.is_loaded = False

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, input_dict: dict) -> dict:
        """
        Run PCOS detection on the given feature dictionary.

        Args:
            input_dict (dict): Feature key-value pairs from the prediction form.

        Returns:
            dict: {"result": "Positive"|"Negative", "confidence": float}
        """
        if self.is_loaded and self.model is not None:
            try:
                import pcos_model
                result, confidence = pcos_model.predict(self.model, input_dict)
                return {
                    "result":     result,
                    "confidence": round(float(confidence), 4),
                }
            except Exception as exc:
                print(f"[ML] ⚠️  Real model prediction failed ({exc}) — falling back to mock.")

        # --- Mock prediction (heuristic placeholder) ---
        return self._mock_predict(input_dict)

    # ------------------------------------------------------------------
    # Mock / heuristic fallback
    # ------------------------------------------------------------------

    def _mock_predict(self, d: dict) -> dict:
        """
        Simple scoring heuristic — used only when pcos_model.pkl is not found.
        Field names match the real 22-feature model inputs.
        """
        score = 0

        # Cycle type: 4 = Irregular (strong PCOS indicator)
        if float(d.get("cycle_type", 2)) == 4:
            score += 3

        # Androgenic / hormonal symptoms
        if float(d.get("skin_darkening", 0)): score += 2
        if float(d.get("hair_growth",    0)): score += 2
        if float(d.get("pimples",        0)): score += 1
        if float(d.get("hair_loss",      0)): score += 1
        if float(d.get("weight_gain",    0)): score += 1

        # Metabolic
        bmi = float(d.get("bmi", 22))
        if bmi > 27: score += 1

        # Ultrasound proxy: follicle count
        if float(d.get("follicle_left",  0)) > 10: score += 3
        if float(d.get("follicle_right", 0)) > 10: score += 3

        # Lifestyle
        if float(d.get("fast_food",    0)): score += 1
        if not float(d.get("reg_exercise", 0)): score += 1

        if score >= 5:
            confidence = min(0.97, 0.55 + (score - 5) * 0.05)
            return {"result": "Positive", "confidence": round(confidence, 4)}
        else:
            confidence = max(0.55, 0.95 - score * 0.07)
            return {"result": "Negative", "confidence": round(confidence, 4)}


# ------------------------------------------------------------------
# Singleton accessor
# ------------------------------------------------------------------

_model_instance: PCOSModel | None = None


def get_model() -> PCOSModel:
    """Return the singleton PCOSModel instance (loads on first call)."""
    global _model_instance
    if _model_instance is None:
        _model_instance = PCOSModel()
    return _model_instance
