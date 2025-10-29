import pandas as pd
import numpy as np
from xgboost import XGBRegressor
import pickle
import os

def create_sample_model():
    """Create a sample XGBoost model for demonstration"""
    
    # Generate sample training data
    np.random.seed(42)
    n_samples = 2000
    
    # Feature columns based on the schema
    data = {
        'Car_Model': np.random.choice(['XC60', 'XC90', 'XC40', 'S60', 'V90'], n_samples),
        'Manufacture_Year': np.random.randint(2018, 2024, n_samples),
        'Fuel_Type': np.random.choice(['Petrol', 'Diesel'], n_samples),
        'Service_Type': np.random.choice(['General', 'Major', 'Brake', 'AC'], n_samples),
        'Total_KM': np.random.randint(5000, 80000, n_samples),
        'KM_Since_Last_Service': np.random.randint(1000, 15000, n_samples),
        'Days_Since_Last_Service': np.random.randint(30, 365, n_samples),
        'Engine_Oil_Change': np.random.randint(0, 2, n_samples),
        'Air_Filter_Replacement': np.random.randint(0, 2, n_samples),
        'Spark_Plugs_Replacement': np.random.randint(0, 2, n_samples),
        'Brake_Pads_Replacement': np.random.randint(0, 2, n_samples),
        'Brake_Fluid_Change': np.random.randint(0, 2, n_samples),
        'Wheel_Alignment': np.random.randint(0, 2, n_samples),
        'Tire_Rotation': np.random.randint(0, 2, n_samples),
        'AC_Service': np.random.randint(0, 2, n_samples),
        'AC_Filter_Replacement': np.random.randint(0, 2, n_samples),
    }
    
    df = pd.DataFrame(data)
    
    # Create target variable (Predicted_Time) based on realistic scenarios
    base_times = {
        'General': 1.5,
        'Major': 3.5,
        'Brake': 2.5,
        'AC': 2.0
    }
    
    # Task time contributions
    task_times = {
        'Engine_Oil_Change': 0.7,
        'Air_Filter_Replacement': 0.4,
        'Spark_Plugs_Replacement': 0.6,
        'Brake_Pads_Replacement': 1.2,
        'Brake_Fluid_Change': 0.8,
        'Wheel_Alignment': 0.9,
        'Tire_Rotation': 0.5,
        'AC_Service': 1.1,
        'AC_Filter_Replacement': 0.3
    }
    
    # Calculate base predicted time
    df['Predicted_Time'] = df['Service_Type'].map(base_times)
    
    # Add task times
    for task, time in task_times.items():
        df['Predicted_Time'] += df[task] * time
    
    # Add complexity factors
    df['Predicted_Time'] += df['Total_KM'] / 50000 * 0.5  # Higher mileage = more time
    df['Predicted_Time'] += df['Days_Since_Last_Service'] / 365 * 0.3  # Longer gap = more time
    
    # Model-specific adjustments
    model_adjustments = {
        'XC90': 0.3,  # Larger vehicle
        'XC60': 0.1,
        'XC40': 0.0,
        'S60': -0.1,
        'V90': 0.2
    }
    df['Predicted_Time'] += df['Car_Model'].map(model_adjustments)
    
    # Fuel type adjustment
    df['Predicted_Time'] += np.where(df['Fuel_Type'] == 'Diesel', 0.2, 0.0)
    
    # Add some random noise
    df['Predicted_Time'] += np.random.normal(0, 0.3, n_samples)
    
    # Ensure realistic bounds
    df['Predicted_Time'] = df['Predicted_Time'].clip(0.5, 8.0)
    
    # Round to 1 decimal place
    df['Predicted_Time'] = df['Predicted_Time'].round(1)
    
    # Prepare features for training
    X = pd.get_dummies(df.drop('Predicted_Time', axis=1))
    y = df['Predicted_Time']
    
    # Train XGBoost model
    model = XGBRegressor(
        n_estimators=150,
        max_depth=8,
        learning_rate=0.1,
        random_state=42,
        subsample=0.8,
        colsample_bytree=0.8
    )
    
    model.fit(X, y)
    
    # Calculate feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("📊 Feature Importance:")
    print(feature_importance.head(10))
    
    # Save the model
    with open('volvo_service_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    # Save sample data for reference
    df.to_csv('data/service_data.csv', index=False)
    
    # Model performance
    train_score = model.score(X, y)
    print(f"✅ Model trained successfully!")
    print(f"📈 Training R² Score: {train_score:.4f}")
    print(f"📊 Samples: {n_samples}")
    print(f"🎯 Time Range: {y.min():.1f} - {y.max():.1f} hours")
    print(f"📁 Model saved: volvo_service_model.pkl")
    print(f"📁 Data saved: data/service_data.csv")
    
    return model, df

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Generate the model
    model, df = create_sample_model()