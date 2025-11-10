🚗 Car Service Time Predictor
Live Demo Python Flask Render

A machine learning web application that predicts car service times based on various factors like vehicle specifications, service type, workshop conditions, and staff availability.

🌐 Live Demo
👉 Try it here: Car Service Time Predictor Web App:[ https://volvo-service-predictor.onrender.com/](https://volvo-service-intelligence-1.onrender.com/)

You can test both:

🧠 Single Prediction: Fill out the form to get instant service time estimates.
📁 Batch Prediction: Upload a CSV file for bulk predictions.
✨ Features
🤖 AI-Powered Predictions – trained on 100,000+ service records
🌐 Web Interface – responsive Flask frontend
📊 Real-time Results – instant time estimation
📁 Batch Processing – upload CSV for multiple predictions
📱 Mobile Responsive – works seamlessly on all devices
💾 Model Persistence – trained model stored with Joblib
📈 Performance Metrics – R², RMSE, MAE, and feature importance
🛠 Tech Stack
Backend
Python 3.11+
Flask – web framework
Scikit-learn, XGBoost, LightGBM – ML models
Pandas & NumPy – data processing
Joblib – model serialization
Frontend
HTML5 / CSS3 / JavaScript
Bootstrap – responsive UI
Chart.js – data visualization
🚀 Installation
Prerequisites
Python 3.11 or higher
pip package manager
Setup Steps
# Clone repository
git clone <repository-url>
cd car_service_predictor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)

# Install dependencies
pip install -r requirements.txt

# Train the model
python train_model.py

# Run Flask app
python app.py
Access the app at http://localhost:5002

📁 Project Structure
car_service_predictor/
│
├── app.py                  # Main Flask application
├── train_model.py          # Model training script
├── requirements.txt        # Dependencies
├── README.md               # Documentation
│
├── models/                 # Trained model storage
│   └── xgboost_car_service_model.pkl
│
├── static/                 # Static files (CSS/JS)
│   ├── css/style.css
│   └── js/script.js
│
├── templates/              # HTML templates
│   ├── base.html
│   ├── index.html
│   └── about.html
│
└── utils/
    └── helpers.py          # Input preprocessing utilities
🎯 Usage
🧩 Single Prediction

Enter vehicle details, service type, workload, and staff info.

Click Predict Service Time to get an instant estimate.

📊 Batch Prediction

Upload a CSV file with multiple records.
Example:

Vehicle_Type,Vehicle_Age,Kilometers_Driven,Service_Type,Number_of_Tasks,Parts_Availability,Appointment_Type,Day_of_Week,Time_of_Day,Mechanic_Experience,Mechanic_Count,Workshop_Workload,Worker_Availability
Sedan,5,50000,Oil Change,3,1,Walk-in,Monday,Morning,5,2,10,2
SUV,3,25000,Full Service,5,1,Scheduled,Friday,Afternoon,8,3,15,3

🌐 API Endpoints
Method	Endpoint	Description
GET	/	Home page
POST	/predict	Single service time prediction
POST	/batch_predict	Batch predictions via CSV
GET	/about	About page
GET	/health	Health check
GET	/debug_models	Debug model info
Example API Call
curl -X POST http://localhost:5002/predict \
  -d "Vehicle_Type=Sedan&Vehicle_Age=5&Kilometers_Driven=50000&Service_Type=Oil_Change&Number_of_Tasks=3&Parts_Availability=1&Appointment_Type=Walk-in&Day_of_Week=Monday&Time_of_Day=Morning&Mechanic_Experience=5&Mechanic_Count=2&Workshop_Workload=10&Worker_Availability=2"

🤖 Model Details

Algorithm: XGBoost Regressor

Training Data: 100,000 synthetic car service records

Features: 13 input + one-hot encoded categorical variables

Target: Estimated service time (hours)

Performance
Metric	Score
R²	> 0.90
RMSE	~0.5 hours
MAE	~0.4 hours
🚀 Deployment
Live App

Deployed on Render Cloud:
🔗 https://car-service-time-predictor-qdw1.onrender.com/

Run in Production (locally)
gunicorn --bind 0.0.0.0:5002 app:app

Docker (optional)
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 5002
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "app:app"]

🧪 Development

Run training and app locally:

python train_model.py
python app.py

📊 Performance Optimization

⚡ Model caching for fast inference

🧮 Efficient preprocessing via NumPy

🔄 Stateless API design for scalability

🧠 Pretrained model artifacts for instant startup

🤝 Contributing

Fork the repository

Create a feature branch (git checkout -b feature/AmazingFeature)

Commit your changes (git commit -m 'Add AmazingFeature')

Push to your branch (git push origin feature/AmazingFeature)

Open a Pull Request

📜 License

Licensed under the MIT License.
See the LICENSE file for details.

🙏 Acknowledgments

Dataset: Synthetic car service records

Icons: Font Awesome

UI Framework: Bootstrap

ML Libraries: Scikit-learn, XGBoost

📞 Support

For any queries or issues:
📧 pradnyeshmagar@gmail.com

📞 +91 9011994315

Made with ❤️ for the automotive service industry.
