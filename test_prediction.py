from utils.predictor import ServicePredictor

def test_prediction():
    predictor = ServicePredictor('volvo_service_model.pkl')
    
    # Test features
    test_features = {
        'Car_Model': 'XC60',
        'Manufacture_Year': 2022,
        'Fuel_Type': 'Petrol',
        'Service_Type': 'General',
        'Total_KM': 35000,
        'KM_Since_Last_Service': 5000,
        'Days_Since_Last_Service': 90,
        'Engine_Oil_Change': 1,
        'Air_Filter_Replacement': 1,
        'Spark_Plugs_Replacement': 0,
        'Brake_Pads_Replacement': 0,
        'Brake_Fluid_Change': 0,
        'Wheel_Alignment': 0,
        'Tire_Rotation': 0,
        'AC_Service': 0,
        'AC_Filter_Replacement': 0
    }
    
    try:
        result = predictor.predict(test_features)
        print(f"✅ Prediction successful: {result} hours")
        return True
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return False

if __name__ == '__main__':
    test_prediction()