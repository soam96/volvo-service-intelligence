from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
from flask_mail import Mail, Message
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import eventlet
import random

from utils.predictor import ServicePredictor
from utils.inventory_manager import InventoryManager
from utils.workload_manager import WorkloadManager
from utils.notifier import Notifier
from utils.report_generator import ReportGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'volvo_service_intelligence_2024_secret_key'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'vsis@volvo.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'password')
app.config['MAIL_DEFAULT_SENDER'] = 'vsis@volvo.com'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
mail = Mail(app)

# Initialize managers
predictor = ServicePredictor('volvo_service_model.pkl')
inventory_manager = InventoryManager('data/inventory.json')
workload_manager = WorkloadManager('data/workload.json')
notifier = Notifier(mail, app)
report_generator = ReportGenerator()

# Service tasks with time estimates
SERVICE_TASKS = {
    'engine_performance': [
        {'id': 'engine_oil', 'name': 'Engine Oil Change', 'time': 0.5},
        {'id': 'air_filter', 'name': 'Air Filter Replacement', 'time': 0.3},
        {'id': 'spark_plugs', 'name': 'Spark Plugs Replacement', 'time': 0.4}
    ],
    'brakes_safety': [
        {'id': 'brake_pads', 'name': 'Brake Pads Replacement', 'time': 0.6},
        {'id': 'brake_fluid', 'name': 'Brake Fluid Change', 'time': 0.5}
    ],
    'wheels_alignment': [
        {'id': 'wheel_alignment', 'name': 'Wheel Alignment', 'time': 0.4},
        {'id': 'tire_rotation', 'name': 'Tire Rotation', 'time': 0.3}
    ],
    'ac_cooling': [
        {'id': 'ac_service', 'name': 'AC Service', 'time': 0.5},
        {'id': 'ac_filter', 'name': 'AC Filter Replacement', 'time': 0.2}
    ]
}

# Parts required for each task
TASK_PARTS = {
    'engine_oil': ['engine_oil', 'oil_filter'],
    'air_filter': ['air_filter'],
    'spark_plugs': ['spark_plugs'],
    'brake_pads': ['brake_pads'],
    'brake_fluid': ['brake_fluid'],
    'wheel_alignment': [],
    'tire_rotation': [],
    'ac_service': ['ac_gas', 'ac_cleaner'],
    'ac_filter': ['ac_filter']
}

# Store active services
active_services = []
completed_services = []

@app.route('/')
def index():
    return render_template('index.html', tasks=SERVICE_TASKS)

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/predict', methods=['POST'])
def predict_service_time():
    try:
        data = request.get_json()
        print(f"📥 Received prediction request: {data}")
        
        # Validate required fields
        required_fields = ['car_model', 'manufacture_year', 'fuel_type', 'service_type', 'number_plate', 'total_km']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({'success': False, 'error': f'Missing required fields: {", ".join(missing_fields)}'})

        # Set default values for optional fields
        km_since_last = data.get('km_since_last_service', 5000)
        days_since_last = data.get('days_since_last_service', 90)
        selected_tasks = data.get('selected_tasks', [])
        
        print(f"🔧 Selected tasks: {selected_tasks}")

        # Prepare features for prediction
        features = {
            'Car_Model': data['car_model'],
            'Manufacture_Year': int(data['manufacture_year']),
            'Fuel_Type': data['fuel_type'],
            'Service_Type': data['service_type'],
            'Total_KM': int(data['total_km']),
            'KM_Since_Last_Service': int(km_since_last),
            'Days_Since_Last_Service': int(days_since_last),
            'Engine_Oil_Change': 1 if 'engine_oil' in selected_tasks else 0,
            'Air_Filter_Replacement': 1 if 'air_filter' in selected_tasks else 0,
            'Spark_Plugs_Replacement': 1 if 'spark_plugs' in selected_tasks else 0,
            'Brake_Pads_Replacement': 1 if 'brake_pads' in selected_tasks else 0,
            'Brake_Fluid_Change': 1 if 'brake_fluid' in selected_tasks else 0,
            'Wheel_Alignment': 1 if 'wheel_alignment' in selected_tasks else 0,
            'Tire_Rotation': 1 if 'tire_rotation' in selected_tasks else 0,
            'AC_Service': 1 if 'ac_service' in selected_tasks else 0,
            'AC_Filter_Replacement': 1 if 'ac_filter' in selected_tasks else 0
        }
        
        # Get prediction
        predicted_time = predictor.predict(features)
        print(f"🎯 Predicted service time: {predicted_time} hours")

        # Assign worker dynamically - NOW RETURNS TWO VALUES
        worker_assignment, service_data_from_worker = workload_manager.assign_worker(
            predicted_time, 
            data['service_type'], 
            data['car_model']
        )
        
        print(f"👷 Worker assignment: {worker_assignment}")

        # Check and deduct inventory
        inventory_status = inventory_manager.check_and_deduct_parts(selected_tasks)
        print(f"📦 Inventory status: {'Available' if inventory_status['available'] else 'Unavailable'}")

        # Use the service ID from the workload manager
        service_id = service_data_from_worker['service_id']

        # Create service record using data from workload manager
        service_data = {
            'service_id': service_id,
            'car_details': data,
            'predicted_time': predicted_time,
            'worker_assigned': worker_assignment,
            'completion_time': worker_assignment.get('completion_time'),
            'inventory_status': inventory_status,
            'status': 'active' if worker_assignment['worker_id'] else 'queued',
            'start_time': datetime.now().isoformat() if worker_assignment.get('immediate_start') else None,
            'timestamp': datetime.now().isoformat()
        }

        # Only add to active_services if it's actually assigned to a worker (not queued)
        if worker_assignment['worker_id']:
            active_services.append(service_data)
            print(f"✅ Added to active services. Total active: {len(active_services)}")
        else:
            print(f"⏳ Service queued. Total queued: {len(workload_manager.service_queue)}")

        # Emit real-time updates
        socketio.emit('workload_update', workload_manager.get_workload_data())
        socketio.emit('inventory_update', inventory_manager.get_inventory_data())
        socketio.emit('service_assigned', service_data)
        socketio.emit('active_services_update', active_services)

        # Check for low stock alerts
        low_stock_parts = inventory_manager.check_low_stock()
        for part in low_stock_parts:
            notifier.send_low_stock_alert(part['name'], part['quantity'])
            socketio.emit('low_stock_alert', {
                'part_name': part['name'],
                'quantity': part['quantity'],
                'timestamp': datetime.now().isoformat()
            })

        return jsonify({
            'success': True,
            'predicted_time': predicted_time,
            'service_id': service_id,
            'worker_assigned': worker_assignment,
            'inventory_status': inventory_status,
            'queue_info': workload_manager.get_queue_info()
        })
        
    except Exception as e:
        error_msg = f'Prediction failed: {str(e)}'
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': error_msg})

@app.route('/generate_report/<service_id>')
def generate_report(service_id):
    try:
        # Find service data
        service_data = next((s for s in completed_services if s['service_id'] == service_id), None)
        if not service_data:
            return jsonify({'error': 'Service not found'}), 404
            
        pdf_path = report_generator.generate_service_report(service_data)
        return send_file(pdf_path, as_attachment=True, download_name=f'{service_id}_report.pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/restock/<part_name>')
def restock_part(part_name):
    try:
        success = inventory_manager.restock_part(part_name, 5)
        if success:
            socketio.emit('inventory_update', inventory_manager.get_inventory_data())
            return jsonify({'success': True, 'message': f'{part_name} restocked successfully'})
        else:
            return jsonify({'success': False, 'error': 'Part not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/complete_service/<service_id>')
def complete_service(service_id):
    try:
        global active_services, completed_services
        
        # Find service in active_services
        service_index = next((i for i, s in enumerate(active_services) if s['service_id'] == service_id), None)
        if service_index is not None:
            service = active_services.pop(service_index)
            service['status'] = 'completed'
            service['completed_at'] = datetime.now().isoformat()
            completed_services.append(service)
            
            # Update worker workload - this will also remove from workload_manager.active_services
            success = workload_manager.complete_service(service_id)
            
            if success:
                # Emit updates
                socketio.emit('workload_update', workload_manager.get_workload_data())
                socketio.emit('active_services_update', active_services)
                socketio.emit('completed_services_update', completed_services[-10:])
                
                print(f"✅ Completed service {service_id}. Active services: {len(active_services)}")
                
                return jsonify({'success': True, 'message': 'Service completed successfully'})
            else:
                return jsonify({'success': False, 'error': 'Failed to complete service in workload manager'})
        else:
            # Service might only be in workload manager (queued or assigned but not in active_services)
            success = workload_manager.complete_service(service_id)
            if success:
                socketio.emit('workload_update', workload_manager.get_workload_data())
                return jsonify({'success': True, 'message': 'Service completed via workload manager'})
            else:
                return jsonify({'success': False, 'error': 'Service not found in active services or workload manager'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# NEW ENDPOINTS ADDED BELOW

@app.route('/admin/sync_data')
def sync_data():
    """Manually sync data between workload manager and active_services"""
    global active_services
    
    # Get current counts for debugging
    workload_active_count = workload_manager.get_active_services_count()
    app_active_count = len(active_services)
    
    print(f"🔄 Syncing data: Workload has {workload_active_count} services, App has {app_active_count} services")
    
    # Clear active_services and rebuild from workload manager
    active_services.clear()
    
    # Rebuild active_services from workload manager data
    all_workload_services = workload_manager.get_all_active_services()
    for service_id, service_info in all_workload_services.items():
        # Create a simplified service record for the app
        active_services.append({
            'service_id': service_id,
            'car_details': {
                'car_model': service_info['job_data']['car_model'],
                'service_type': service_info['job_data']['service_type']
            },
            'predicted_time': service_info['job_data']['original_duration'],
            'worker_assigned': {
                'worker_id': service_info['worker_id'],
                'worker_name': service_info['worker_name'],
                'completion_time': service_info['job_data']['completion_time']
            },
            'status': 'active',
            'start_time': service_info['job_data']['start_time'],
            'timestamp': service_info['job_data']['assigned_at']
        })
    
    # Also add queued services
    for queue_item in workload_manager.service_queue:
        active_services.append({
            'service_id': queue_item['service_id'],
            'car_details': {
                'car_model': queue_item['car_model'],
                'service_type': queue_item['service_type']
            },
            'predicted_time': queue_item['job_duration'],
            'worker_assigned': {
                'worker_name': 'Queue',
                'queue_position': workload_manager.service_queue.index(queue_item) + 1,
                'estimated_wait_time': queue_item['estimated_wait_time']
            },
            'status': 'queued',
            'timestamp': queue_item['added_to_queue']
        })
    
    socketio.emit('active_services_update', active_services)
    socketio.emit('workload_update', workload_manager.get_workload_data())
    
    return jsonify({
        'success': True, 
        'message': f'Data synced. Active services: {len(active_services)}',
        'workload_active_services': workload_active_count,
        'app_active_services': len(active_services),
        'queued_services': len(workload_manager.service_queue)
    })

@app.route('/admin/reset_all')
def reset_all():
    """Reset all data for testing"""
    global active_services, completed_services
    
    # Clear all services
    active_services.clear()
    completed_services.clear()
    
    # Reset workload manager using the new method
    workload_manager.reset_all()
    
    # Reset inventory
    inventory_manager.load_inventory()
    
    socketio.emit('workload_update', workload_manager.get_workload_data())
    socketio.emit('inventory_update', inventory_manager.get_inventory_data())
    socketio.emit('active_services_update', active_services)
    socketio.emit('completed_services_update', completed_services)
    
    return jsonify({
        'success': True, 
        'message': 'All data reset successfully',
        'active_services': len(active_services),
        'workload_active_services': workload_manager.get_active_services_count()
    })

@app.route('/api/debug/workload')
def debug_workload():
    """Debug endpoint to see actual workload data"""
    workload_data = workload_manager.get_workload_data()
    
    debug_info = {
        'raw_workload_data': workload_data,
        'active_services_count': len(active_services),
        'workload_active_services_count': workload_manager.get_active_services_count(),
        'active_services_details': [
            {
                'service_id': service['service_id'],
                'worker': service['worker_assigned']['worker_name'] if service['worker_assigned'] else 'Queued',
                'status': service['status']
            }
            for service in active_services
        ],
        'workers_details': [
            {
                'id': worker['id'],
                'name': worker['name'],
                'current_jobs_count': len(worker['current_jobs']),
                'current_jobs': [job['service_id'] for job in worker['current_jobs']],
                'current_workload': worker['current_workload']
            }
            for worker in workload_manager.workers
        ],
        'workload_active_services': workload_manager.get_all_active_services(),
        'queued_services': workload_manager.service_queue
    }
    
    return jsonify(debug_info)

@app.route('/api/debug/sync_check')
def debug_sync_check():
    """Check if data is synchronized"""
    workload_count = workload_manager.get_active_services_count()
    app_count = len(active_services)
    
    is_synced = workload_count == app_count
    
    return jsonify({
        'workload_active_services': workload_count,
        'app_active_services': app_count,
        'is_synchronized': is_synced,
        'difference': abs(workload_count - app_count),
        'message': 'SYNCED' if is_synced else 'OUT OF SYNC'
    })

# EXISTING ENDPOINTS

@app.route('/api/workload')
def api_workload():
    return jsonify(workload_manager.get_workload_data())

@app.route('/api/inventory')
def api_inventory():
    return jsonify(inventory_manager.get_inventory_data())

@app.route('/api/active_services')
def api_active_services():
    return jsonify(active_services)

@app.route('/api/completed_services')
def api_completed_services():
    return jsonify(completed_services[-10:])  # Return last 10

@socketio.on('connect')
def handle_connect():
    emit('workload_update', workload_manager.get_workload_data())
    emit('inventory_update', inventory_manager.get_inventory_data())
    emit('active_services_update', active_services)
    emit('completed_services_update', completed_services[-10:])

def ensure_directories():
    """Ensure all required directories exist"""
    directories = ['data', 'reports', 'static/css', 'static/js', 'templates', 'utils']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Directory ensured: {directory}")
    
    # Ensure data files exist
    data_files = ['data/inventory.json', 'data/workload.json', 'data/services.json']
    for file_path in data_files:
        if not os.path.exists(file_path):
            # Create empty files if they don't exist
            with open(file_path, 'w') as f:
                json.dump({}, f)
            print(f"✅ Created data file: {file_path}")

def ensure_ml_model():
    """Create ML model if it doesn't exist"""
    if not os.path.exists('volvo_service_model.pkl'):
        print("🤖 Creating sample ML model...")
        from create_model import create_sample_model
        create_sample_model()
        print("✅ ML model created successfully!")

if __name__ == '__main__':
    ensure_directories()
    ensure_ml_model()
    print("🚀 Starting Volvo Service Intelligence System...")
    print("📍 User Panel: http://localhost:5001")
    print("📍 Admin Dashboard: http://localhost:5001/admin")
    
    # NEW: Debug URLs
    print("🔧 Debug Endpoints:")
    print("   - Sync Data: http://localhost:5001/admin/sync_data")
    print("   - Reset All: http://localhost:5001/admin/reset_all")
    print("   - Debug Workload: http://localhost:5001/api/debug/workload")
    print("   - Sync Check: http://localhost:5001/api/debug/sync_check")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)