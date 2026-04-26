import os
import joblib
import pandas as pd

# Path configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "training", "model.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "training", "encoder.joblib")
FEATURES_PATH = os.path.join(BASE_DIR, "training", "features.joblib")

def get_ml_features(state):
    """Extracts features from the environment state for ML model."""
    events = state.get("events", [])
    prof_events = [e for e in events if e.get("domain") == "professional"]
    pers_events = [e for e in events if e.get("domain") == "personal"]
    
    prof_high = any(e for e in prof_events if e.get("priority") == "high")
    pers_high = any(e for e in pers_events if e.get("priority") == "high")
    
    state_summary = "double_high_conflict" if (prof_high and pers_high) else "prof_dominant" if prof_high else "pers_dominant" if pers_high else "balanced_conflict"
    
    return {
        "prof_count": len(prof_events),
        "pers_count": len(pers_events),
        "prof_high_prio": 1 if prof_high else 0,
        "pers_high_prio": 1 if pers_high else 0,
        "any_inflexible": 1 if any(not e.get("flexible") for e in events) else 0,
        "conflict_detected": 1 if state.get("has_conflict") else 0,
        "state_summary": state_summary
    }

def predict_ml_action(features):
    """
    Predicts action and returns (action, confidence).
    Confidence is simulated as the max probability from the classifier.
    """
    if not os.path.exists(MODEL_PATH):
        return None, 0.0

    try:
        model = joblib.load(MODEL_PATH)
        le = joblib.load(ENCODER_PATH)
        feature_names = joblib.load(FEATURES_PATH)

        # Prepare input
        df_input = pd.DataFrame([features])
        df_input = pd.get_dummies(df_input)
        
        # Align features
        for col in feature_names:
            if col not in df_input.columns:
                df_input[col] = 0
        df_input = df_input[feature_names]

        # Get probabilities for confidence
        probs = model.predict_proba(df_input)[0]
        max_prob = max(probs)
        
        prediction_encoded = model.predict(df_input)
        action = le.inverse_transform(prediction_encoded)[0]
        
        return action, max_prob
    except Exception as e:
        print(f"ML Prediction Error: {e}")
        return None, 0.0
