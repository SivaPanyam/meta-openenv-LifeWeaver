import json
import pandas as pd
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib

def train_model():
    dataset_path = "backend/training/dataset.json"
    model_path = "backend/training/model.pkl"
    encoder_path = "backend/training/encoder.joblib"

    if not os.path.exists(dataset_path):
        print("Error: dataset.json not found.")
        return

    with open(dataset_path, "r") as f:
        data = json.load(f)

    if not data:
        print("Error: dataset is empty.")
        return

    # Convert to DataFrame
    df_list = []
    for entry in data:
        row = entry["input"].copy()
        row["output"] = entry["output"]
        df_list.append(row)
    
    df = pd.DataFrame(df_list)

    # Encode target (output)
    le = LabelEncoder()
    df["output_encoded"] = le.fit_transform(df["output"])
    
    # Encode categorical features
    # state_summary is categorical
    df = pd.get_dummies(df, columns=["state_summary"])

    # Features and Target
    X = df.drop(columns=["output", "output_encoded"])
    y = df["output_encoded"]

    # Train Classifier
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    # Save Model, Encoder, and Feature Names
    joblib.dump(model, model_path)
    joblib.dump(le, encoder_path)
    joblib.dump(X.columns.tolist(), "backend/training/features.joblib")

    print(f"✅ Model trained and saved to {model_path}")

def predict_action(state_features):
    """
    Predicts the best action from state features.
    state_features should be a dict matching the input format.
    """
    model = joblib.load("backend/training/model.pkl")
    le = joblib.load("backend/training/encoder.joblib")
    feature_names = joblib.load("backend/training/features.joblib")

    # Prepare input
    df_input = pd.DataFrame([state_features])
    df_input = pd.get_dummies(df_input)
    
    # Ensure all training features are present (alignment)
    for col in feature_names:
        if col not in df_input.columns:
            df_input[col] = 0
    
    df_input = df_input[feature_names]

    prediction_encoded = model.predict(df_input)
    return le.inverse_transform(prediction_encoded)[0]

if __name__ == "__main__":
    train_model()
    
    # Quick Test
    test_state = {
        "prof_count": 2,
        "pers_count": 2,
        "prof_high_prio": 1,
        "pers_high_prio": 1,
        "any_inflexible": 1,
        "conflict_detected": 1,
        "state_summary": "double_high_conflict"
    }
    print(f"Test Prediction: {predict_action(test_state)}")
