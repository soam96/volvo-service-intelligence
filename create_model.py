import pandas as pd
import numpy as np
from xgboost import XGBRegressor
import pickle
import os


# ---------------------------------------------------------
# ✅ Ultra-Realistic Volvo Service Dataset Generator
# ---------------------------------------------------------
def generate_ultra_realistic_volvo_data(n_samples=2000):
    np.random.seed(42)

    car_models = ['XC60', 'XC90', 'XC40', 'S60', 'V90']

    # --- Realistic mileage distribution ---
    total_km = np.concatenate([
        np.random.randint(10000, 20000, int(n_samples * 0.15)),
        np.random.randint(20000, 60000, int(n_samples * 0.40)),
        np.random.randint(60000, 180000, int(n_samples * 0.45)),
    ])
    np.random.shuffle(total_km)

    # Manufacture year depends on running
    manufacture_year = np.where(
        total_km > 120000,
        np.random.randint(2015, 2019),
        np.random.choice([2019, 2020, 2021, 2022, 2023], n_samples)
    )

    # KM since last service = 6–20% of total
    km_last = (total_km * np.random.uniform(0.06, 0.20, n_samples)).astype(int)

    # Days since last service
    days_last = np.where(
        manufacture_year >= 2021,
        np.random.randint(60, 200, n_samples),
        np.random.randint(90, 365, n_samples)
    )

    service_type = np.random.choice(
        ['General', 'Major', 'Brake', 'AC'],
        n_samples,
        p=[0.50, 0.25, 0.15, 0.10]
    )

    df = pd.DataFrame({
        'Car_Model': np.random.choice(car_models, n_samples),
        'Manufacture_Year': manufacture_year,
        'Fuel_Type': np.random.choice(['Petrol', 'Diesel'], n_samples, p=[0.65, 0.35]),
        'Service_Type': service_type,
        'Total_KM': total_km,
        'KM_Since_Last_Service': km_last,
        'Days_Since_Last_Service': days_last,
    })

    # ----------------------------------------------------
    # 🔧 OEM-Realistic Service Logic (No change here)
    # ----------------------------------------------------

    df['Engine_Oil_Change'] = (df['KM_Since_Last_Service'] > 10000).astype(int)
    df['Air_Filter_Replacement'] = (df['KM_Since_Last_Service'] > 15000).astype(int)

    df['Spark_Plugs_Replacement'] = np.where(
        (df['Fuel_Type'] == 'Petrol') &
        (df['Total_KM'] > np.random.randint(40000, 60000)),
        1, 0
    )

    df['Brake_Pads_Replacement'] = (df['Total_KM'] > np.random.randint(30000, 45000, n_samples)).astype(int)
    df['Brake_Fluid_Change'] = (df['Days_Since_Last_Service'] > 280).astype(int)

    df['Wheel_Alignment'] = np.where(
        total_km > 80000,
        np.random.choice([0,1], n_samples, p=[0.3,0.7]),
        np.random.choice([0,1], n_samples, p=[0.6,0.4])
    )

    df['Tire_Rotation'] = (df['KM_Since_Last_Service'] > 8000).astype(int)

    df['AC_Service'] = np.where(
        (df['Service_Type'] == 'AC') |
        (df['Days_Since_Last_Service'] > np.random.randint(300, 450)),
        1, 0
    )

    df['AC_Filter_Replacement'] = np.where(
        (df['AC_Service'] == 1) & (df['Total_KM'] > 50000),
        1, 0
    )

    major = df['Service_Type'] == 'Major'
    df.loc[major, ['Engine_Oil_Change', 'Air_Filter_Replacement', 'Brake_Fluid_Change']] = 1

    brake = df['Service_Type'] == 'Brake'
    df.loc[brake, ['Brake_Pads_Replacement', 'Brake_Fluid_Change']] = 1

    ac = df['Service_Type'] == 'AC'
    df.loc[ac, 'AC_Service'] = 1

    # ---------------------------------------------------------
    # ⭐ NEW: Add Realistic Workload & 48-Hour Time Estimation
    # ---------------------------------------------------------

    # Cars already waiting in the queue at service center
    df["Workload_Cars_Pending"] = np.random.randint(1, 25, n_samples)

    # Base service time (in hours)
    realistic_base = {
        "General": np.random.randint(4, 8),
        "Major": np.random.randint(10, 18),
        "Brake": np.random.randint(3, 7),
        "AC": np.random.randint(2, 6),
    }

    df["Base_Service_Hours"] = df["Service_Type"].apply(lambda x: realistic_base[x])

    # Workload adds 0.4 – 1 hour per car in queue
    df["Workload_Delay_Hours"] = (df["Workload_Cars_Pending"] *
                                  np.random.uniform(0.4, 1.0, n_samples)).round(1)

    # Final calculated realistic time
    df["Final_Service_Time_Hours"] = (
        df["Base_Service_Hours"] +
        df["Workload_Delay_Hours"]
    ).clip(2, 48).round(1)

    return df


# ---------------------------------------------------------
# ✅ ML Model Training
# ---------------------------------------------------------
def create_sample_model():

    print("\n🚀 Generating ultra-realistic Volvo dataset...")
    df = generate_ultra_realistic_volvo_data(2000)

    # ML Predicted_Time (kept at 0–9 hrs range for model)
    base_times = {
        'General': 1.5,
        'Major': 3.8,
        'Brake': 2.6,
        'AC': 1.9
    }

    task_times = {
        'Engine_Oil_Change': 0.7,
        'Air_Filter_Replacement': 0.4,
        'Spark_Plugs_Replacement': 0.6,
        'Brake_Pads_Replacement': 1.2,
        'Brake_Fluid_Change': 0.9,
        'Wheel_Alignment': 1.0,
        'Tire_Rotation': 0.5,
        'AC_Service': 1.0,
        'AC_Filter_Replacement': 0.4
    }

    df['Predicted_Time'] = df['Service_Type'].map(base_times)

    for task, time in task_times.items():
        df['Predicted_Time'] += df[task] * time

    df['Predicted_Time'] += df['Total_KM'] / 60000 * 0.4
    df['Predicted_Time'] += df['Days_Since_Last_Service'] / 365 * 0.25

    model_adj = {'XC90': 0.35, 'XC60': 0.15, 'XC40': 0.00, 'S60': -0.10, 'V90': 0.25}
    df['Predicted_Time'] += df['Car_Model'].map(model_adj)

    df['Predicted_Time'] += np.where(df['Fuel_Type'] == 'Diesel', 0.2, 0)

    df['Predicted_Time'] += np.random.normal(0, 0.25, len(df))
    df['Predicted_Time'] = df['Predicted_Time'].clip(0.8, 9.0).round(1)

    X = pd.get_dummies(df.drop('Predicted_Time', axis=1))
    y = df['Predicted_Time']

    model = XGBRegressor(
        n_estimators=160,
        max_depth=8,
        learning_rate=0.1,
        random_state=42,
        subsample=0.85,
        colsample_bytree=0.85
    )
    model.fit(X, y)

    print("\n📊 Top 10 Important Features:")
    importance = pd.Series(model.feature_importances_, index=X.columns)
    print(importance.sort_values(ascending=False).head(10))

    print("\n📈 Training Accuracy (R²):", model.score(X, y))

    os.makedirs("data", exist_ok=True)

    with open("volvo_service_model.pkl", "wb") as f:
        pickle.dump(model, f)

    df.to_csv("data/service_data.csv", index=False)

    print("\n✅ Model saved as: volvo_service_model.pkl")
    print("📁 Dataset saved as: data/service_data.csv")

    return model, df


if __name__ == '__main__':
    create_sample_model()
