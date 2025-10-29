import pandas as pd
import numpy as np
import pickle

class ServicePredictor:
    def __init__(self, model_path):
        self.model_path = model_path
        self.model = None
        self.training_columns = None
        self.load_model()
    
    def load_model(self):
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            # Define the exact column order the model expects
            self.training_columns = [
                'Manufacture_Year', 'Total_KM', 'KM_Since_Last_Service', 'Days_Since_Last_Service',
                'Engine_Oil_Change', 'Air_Filter_Replacement', 'Spark_Plugs_Replacement',
                'Brake_Pads_Replacement', 'Brake_Fluid_Change', 'Wheel_Alignment',
                'Tire_Rotation', 'AC_Service', 'AC_Filter_Replacement',
                'Car_Model_S60', 'Car_Model_V90', 'Car_Model_XC40', 'Car_Model_XC60', 'Car_Model_XC90',
                'Fuel_Type_Diesel', 'Fuel_Type_Petrol',
                'Service_Type_AC', 'Service_Type_Brake', 'Service_Type_General', 'Service_Type_Major'
            ]
            print("✅ ML model loaded successfully")
        except Exception as e:
            print(f"⚠️ Could not load ML model: {e}")
            print("🔄 Using reliable rule-based prediction")
            self.model = None
    
    def predict(self, features):
        # Always use rule-based prediction for now to ensure reliability
        return self.rule_based_prediction(features)
    
    def ml_predict(self, features):
        """ML prediction - kept separate for future use"""
        if self.model is None:
            return None
            
        try:
            # Create feature dictionary with all expected columns
            feature_dict = {
                'Manufacture_Year': features['Manufacture_Year'],
                'Total_KM': features['Total_KM'],
                'KM_Since_Last_Service': features['KM_Since_Last_Service'],
                'Days_Since_Last_Service': features['Days_Since_Last_Service'],
                'Engine_Oil_Change': features['Engine_Oil_Change'],
                'Air_Filter_Replacement': features['Air_Filter_Replacement'],
                'Spark_Plugs_Replacement': features['Spark_Plugs_Replacement'],
                'Brake_Pads_Replacement': features['Brake_Pads_Replacement'],
                'Brake_Fluid_Change': features['Brake_Fluid_Change'],
                'Wheel_Alignment': features['Wheel_Alignment'],
                'Tire_Rotation': features['Tire_Rotation'],
                'AC_Service': features['AC_Service'],
                'AC_Filter_Replacement': features['AC_Filter_Replacement'],
                
                # One-hot encoded columns
                'Car_Model_S60': 1 if features['Car_Model'] == 'S60' else 0,
                'Car_Model_V90': 1 if features['Car_Model'] == 'V90' else 0,
                'Car_Model_XC40': 1 if features['Car_Model'] == 'XC40' else 0,
                'Car_Model_XC60': 1 if features['Car_Model'] == 'XC60' else 0,
                'Car_Model_XC90': 1 if features['Car_Model'] == 'XC90' else 0,
                
                'Fuel_Type_Diesel': 1 if features['Fuel_Type'] == 'Diesel' else 0,
                'Fuel_Type_Petrol': 1 if features['Fuel_Type'] == 'Petrol' else 0,
                
                'Service_Type_AC': 1 if features['Service_Type'] == 'AC' else 0,
                'Service_Type_Brake': 1 if features['Service_Type'] == 'Brake' else 0,
                'Service_Type_General': 1 if features['Service_Type'] == 'General' else 0,
                'Service_Type_Major': 1 if features['Service_Type'] == 'Major' else 0,
            }
            
            # Create DataFrame with exact column order
            feature_df = pd.DataFrame([feature_dict])[self.training_columns]
            
            prediction = self.model.predict(feature_df)[0]
            return max(0.5, float(prediction))
            
        except Exception as e:
            print(f"❌ ML prediction error: {e}")
            return None
    
    def rule_based_prediction(self, features):
        """Reliable rule-based prediction that always works"""
        print(f"🔧 Using rule-based prediction for: {features['Car_Model']} {features['Service_Type']} service")
        
        # Base service times (hours)
        base_times = {
            'General': 2.0,
            'Major': 4.0,
            'Brake': 3.0,
            'AC': 2.5
        }
        
        base_time = base_times.get(features['Service_Type'], 2.5)
        
        # Individual task times (hours)
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
        
        # Calculate total task time
        task_time = 0
        for task, time in task_times.items():
            if features.get(task, 0) == 1:
                task_time += time
                print(f"   - {task}: +{time}h")
        
        # Vehicle model adjustments
        model_adjustments = {
            'XC90': 0.4,  # Larger, more complex
            'XC60': 0.2,
            'XC40': 0.0,
            'S60': -0.1,  # Smaller, simpler
            'V90': 0.3
        }
        model_adj = model_adjustments.get(features['Car_Model'], 0.0)
        
        # Fuel type adjustments
        fuel_adj = 0.3 if features['Fuel_Type'] == 'Diesel' else 0.0
        
        # Mileage factor (older/higher mileage cars take longer)
        mileage_factor = min(features['Total_KM'] / 100000, 1.0) * 0.5
        
        # Calculate total time
        total_time = base_time + task_time + model_adj + fuel_adj + mileage_factor
        
        # Add small random variation for realism (±15%)
        variation = np.random.uniform(-0.15, 0.15) * total_time
        total_time += variation
        
        # Ensure reasonable bounds (0.5 to 8 hours)
        final_time = max(0.5, min(8.0, total_time))
        final_time = round(final_time, 2)
        
        print(f"   Base: {base_time}h, Tasks: {task_time}h, Model: {model_adj}h")
        print(f"   Fuel: {fuel_adj}h, Mileage: {mileage_factor}h")
        print(f"   Total: {final_time}h")
        
        return final_time