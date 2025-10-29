import json
from datetime import datetime, timedelta
import random

class WorkloadManager:
    def __init__(self, workload_file):
        self.workload_file = workload_file
        self.workers = []
        self.active_services = {}
        self.service_queue = []  # Queue for services waiting for workers
        self.load_workload()
    
    def load_workload(self):
        try:
            with open(self.workload_file, 'r') as f:
                data = json.load(f)
                self.workers = data.get('workers', [])
                self.active_services = data.get('active_services', {})
                self.service_queue = data.get('service_queue', [])
            
            # Migrate existing data to include new fields
            self.migrate_worker_data()
            
            print(f"✅ Workload loaded successfully with {len(self.workers)} workers")
            print(f"📊 Current active services: {len(self.active_services)}, Queued services: {len(self.service_queue)}")
        except Exception as e:
            print(f"⚠️ Could not load workload data: {e}")
            print("🔄 Initializing with default workers...")
            self.initialize_default_workers()
            self.save_workload()
    
    def migrate_worker_data(self):
        """Migrate existing worker data to include new fields"""
        migrated = False
        for worker in self.workers:
            # Add missing fields with default values
            if 'max_concurrent_jobs' not in worker:
                worker['max_concurrent_jobs'] = 3
                migrated = True
            
            if 'specialization' not in worker:
                # Assign specialization based on worker ID
                worker_id_num = int(worker['id'][1:])  # Extract number from W01, W02, etc.
                if worker_id_num <= 5:
                    worker['specialization'] = 'Engine Specialist'
                elif worker_id_num <= 10:
                    worker['specialization'] = 'Brake Expert'
                elif worker_id_num <= 15:
                    worker['specialization'] = 'AC Technician'
                else:
                    worker['specialization'] = 'General Maintenance'
                migrated = True
            
            if 'efficiency' not in worker:
                worker['efficiency'] = round(random.uniform(0.8, 1.2), 2)
                migrated = True
            
            if 'rating' not in worker:
                worker['rating'] = round(random.uniform(4.0, 5.0), 1)
                migrated = True
            
            if 'experience_years' not in worker:
                worker['experience_years'] = random.randint(1, 15)
                migrated = True
        
        if migrated:
            print("🔄 Migrated worker data to new format")
            self.save_workload()
    
    def initialize_default_workers(self):
        """Initialize with 20 default workers"""
        self.workers = []
        first_names = ['Alex', 'Brian', 'Chris', 'David', 'Eric', 'Frank', 'George', 'Henry', 'Ian', 'John', 
                      'Kevin', 'Liam', 'Mike', 'Nathan', 'Oscar', 'Paul', 'Quinn', 'Ryan', 'Steve', 'Tom']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Miller', 'Davis', 'Garcia', 'Rodriguez', 'Wilson',
                     'Martinez', 'Anderson', 'Taylor', 'Thomas', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White']
        
        for i in range(1, 21):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            # Assign specializations based on worker ID ranges
            if i <= 5:
                specialization = 'Engine Specialist'
            elif i <= 10:
                specialization = 'Brake Expert'
            elif i <= 15:
                specialization = 'AC Technician'
            else:
                specialization = 'General Maintenance'
            
            self.workers.append({
                'id': f'W{i:02d}',
                'name': f'{first_name} {last_name}',
                'specialization': specialization,
                'current_jobs': [],
                'total_capacity': 8,  # hours per day
                'current_workload': 0,
                'max_concurrent_jobs': 3,  # Each worker can handle multiple cars
                'efficiency': round(random.uniform(0.8, 1.2), 2),
                'rating': round(random.uniform(4.0, 5.0), 1),
                'experience_years': random.randint(1, 15),
                'is_available': True
            })
        
        print(f"✅ Initialized {len(self.workers)} default workers")
    
    def save_workload(self):
        try:
            data = {
                'workers': self.workers,
                'active_services': self.active_services,
                'service_queue': self.service_queue,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.workload_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving workload: {e}")
    
    def get_available_workers(self, required_specialization=None):
        """Get list of available workers who can take more jobs"""
        available_workers = []
        
        for worker in self.workers:
            # Ensure worker has the required field
            if 'max_concurrent_jobs' not in worker:
                worker['max_concurrent_jobs'] = 3  # Default value
            
            # Check if worker has capacity for more jobs
            can_take_more_jobs = (
                len(worker['current_jobs']) < worker['max_concurrent_jobs'] and
                worker['current_workload'] < worker['total_capacity'] - 2  # Leave 2 hours buffer
            )
            
            # Check specialization match if required
            specialization_match = (
                not required_specialization or 
                required_specialization in worker['specialization'] or
                worker['specialization'] == 'General Maintenance'
            )
            
            if can_take_more_jobs and specialization_match:
                available_workers.append(worker)
        
        return available_workers
    
    def assign_worker(self, job_duration, service_type=None, car_model=None):
        """Assign a worker to a job, considering multiple concurrent jobs"""
        # Ensure workers list is not empty
        if not self.workers:
            print("⚠️ No workers available, initializing default workers...")
            self.initialize_default_workers()
        
        # Determine required specialization based on service type
        specialization_map = {
            'General': 'General Maintenance',
            'Major': 'Engine Specialist',
            'Brake': 'Brake Expert',
            'AC': 'AC Technician'
        }
        required_specialization = specialization_map.get(service_type, 'General Maintenance')
        
        print(f"🔧 Looking for {required_specialization} for {service_type} service on {car_model}")
        
        # Get available workers
        available_workers = self.get_available_workers(required_specialization)
        
        if available_workers:
            # Strategy 1: Prefer workers with matching specialization and lowest workload
            best_worker = None
            best_score = float('-inf')
            
            for worker in available_workers:
                # Calculate score for worker selection
                score = 0
                
                # Specialization match bonus
                if required_specialization in worker['specialization']:
                    score += 50
                elif worker['specialization'] == 'General Maintenance':
                    score += 25
                
                # Lower workload is better
                workload_bonus = (worker['total_capacity'] - worker['current_workload']) * 10
                score += workload_bonus
                
                # Fewer current jobs is better
                jobs_bonus = (worker['max_concurrent_jobs'] - len(worker['current_jobs'])) * 20
                score += jobs_bonus
                
                # Efficiency bonus
                efficiency_bonus = (worker['efficiency'] - 1) * 30
                score += efficiency_bonus
                
                if score > best_score:
                    best_score = score
                    best_worker = worker
            
            if best_worker:
                return self.assign_to_worker(best_worker, job_duration, service_type, car_model)
        
        # Strategy 2: If no specialized workers available, try general maintenance workers
        if required_specialization != 'General Maintenance':
            general_workers = self.get_available_workers('General Maintenance')
            if general_workers:
                # Pick the general worker with lowest workload
                general_workers.sort(key=lambda w: w['current_workload'])
                return self.assign_to_worker(general_workers[0], job_duration, service_type, car_model)
        
        # Strategy 3: If still no workers, find anyone with capacity
        all_available = self.get_available_workers()
        if all_available:
            all_available.sort(key=lambda w: w['current_workload'])
            return self.assign_to_worker(all_available[0], job_duration, service_type, car_model)
        
        # Strategy 4: If no workers available at all, add to queue
        return self.add_to_queue(job_duration, service_type, car_model)
    
    def assign_to_worker(self, worker, job_duration, service_type, car_model):
        """Assign a specific job to a worker and return both assignment info and service data"""
        # Ensure worker has required fields
        if 'max_concurrent_jobs' not in worker:
            worker['max_concurrent_jobs'] = 3
        
        if 'efficiency' not in worker:
            worker['efficiency'] = 1.0
        
        # Adjust job duration by worker efficiency
        adjusted_duration = job_duration / worker['efficiency']
        
        # Calculate start time (can be now or later based on current workload)
        start_time = datetime.now()
        if worker['current_jobs']:
            # Find the earliest available slot
            latest_completion = max([
                datetime.fromisoformat(job['completion_time']) 
                for job in worker['current_jobs']
            ])
            start_time = max(start_time, latest_completion)
        
        completion_time = start_time + timedelta(hours=adjusted_duration)
        
        # Generate service ID
        service_id = f"VOL_{datetime.now().strftime('%Y%m%d%H%M%S')}{worker['id']}"
        
        # Add job to worker
        job_data = {
            'service_id': service_id,
            'car_model': car_model,
            'service_type': service_type,
            'start_time': start_time.isoformat(),
            'completion_time': completion_time.isoformat(),
            'duration': adjusted_duration,
            'original_duration': job_duration,
            'assigned_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        worker['current_jobs'].append(job_data)
        worker['current_workload'] = sum(job['duration'] for job in worker['current_jobs'])
        
        # Store in active services
        self.active_services[service_id] = {
            'worker_id': worker['id'],
            'worker_name': worker['name'],
            'job_data': job_data
        }
        
        self.save_workload()
        
        print(f"✅ Assigned service to {worker['name']} ({worker['specialization']})")
        print(f"   📊 Worker now has {len(worker['current_jobs'])} jobs, {worker['current_workload']:.1f}h workload")
        print(f"   ⏰ Completion: {completion_time.strftime('%Y-%m-%d %H:%M')}")
        
        # Return both assignment info AND service data for app.py to use
        assignment_info = {
            'worker_id': worker['id'],
            'worker_name': worker['name'],
            'specialization': worker['specialization'],
            'efficiency': worker['efficiency'],
            'rating': worker.get('rating', 4.5),
            'completion_time': completion_time.isoformat(),
            'adjusted_duration': round(adjusted_duration, 2),
            'workload_percentage': (worker['current_workload'] / worker['total_capacity']) * 100,
            'current_jobs_count': len(worker['current_jobs']),
            'queue_position': 0,  # Not in queue
            'immediate_start': len(worker['current_jobs']) == 1  # Immediate start if first job
        }
        
        # Also return the service data that should be added to active_services
        service_data = {
            'service_id': service_id,
            'worker_assigned': assignment_info,
            'job_data': job_data
        }
        
        return assignment_info, service_data
    
    def add_to_queue(self, job_duration, service_type, car_model):
        """Add service to queue when no workers are available and return both assignment info and service data"""
        service_id = f"QUEUE_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        queue_item = {
            'service_id': service_id,
            'car_model': car_model,
            'service_type': service_type,
            'job_duration': job_duration,
            'added_to_queue': datetime.now().isoformat(),
            'estimated_wait_time': self.estimate_wait_time()
        }
        
        self.service_queue.append(queue_item)
        self.save_workload()
        
        queue_position = len(self.service_queue)
        estimated_wait = self.estimate_wait_time()
        
        print(f"⏳ Service added to queue. Position: {queue_position}, Estimated wait: {estimated_wait}h")
        
        assignment_info = {
            'worker_id': None,
            'worker_name': 'Queue',
            'specialization': 'Waiting',
            'completion_time': None,
            'adjusted_duration': job_duration,
            'workload_percentage': 0,
            'current_jobs_count': 0,
            'queue_position': queue_position,
            'estimated_wait_time': estimated_wait,
            'immediate_start': False
        }
        
        service_data = {
            'service_id': service_id,
            'worker_assigned': assignment_info,
            'is_queued': True
        }
        
        return assignment_info, service_data
    
    def estimate_wait_time(self):
        """Estimate wait time for queued services"""
        if not self.workers:
            return 4.0  # Default estimate
        
        # Calculate average completion time of current jobs
        total_remaining_time = 0
        active_jobs = 0
        
        for worker in self.workers:
            for job in worker['current_jobs']:
                completion_time = datetime.fromisoformat(job['completion_time'])
                remaining_time = (completion_time - datetime.now()).total_seconds() / 3600
                if remaining_time > 0:
                    total_remaining_time += remaining_time
                    active_jobs += 1
        
        if active_jobs == 0:
            return 1.0  # Minimal wait if no active jobs
        
        avg_remaining = total_remaining_time / active_jobs
        queue_length = len(self.service_queue)
        
        # Estimate: average remaining time + 1 hour per queued job
        estimated_wait = avg_remaining + (queue_length * 1.0)
        
        return min(estimated_wait, 8.0)  # Cap at 8 hours
    
    def process_queue(self):
        """Process queued services when workers become available"""
        processed = []
        
        for queue_item in self.service_queue[:]:  # Copy for safe iteration
            available_workers = self.get_available_workers()
            if available_workers:
                # Assign this queued service
                worker_assignment, service_data = self.assign_to_worker(
                    available_workers[0],
                    queue_item['job_duration'],
                    queue_item['service_type'],
                    queue_item['car_model']
                )
                
                # Update the service ID to match the original queue item if needed
                if worker_assignment:
                    self.service_queue.remove(queue_item)
                    processed.append({
                        'original_queue_item': queue_item,
                        'worker_assignment': worker_assignment,
                        'service_data': service_data
                    })
                    print(f"🚀 Processed queued service: {queue_item['car_model']} {queue_item['service_type']}")
        
        self.save_workload()
        return processed
    
    def complete_service(self, service_id):
        """Mark a service as completed and remove from worker's workload"""
        if service_id in self.active_services:
            worker_id = self.active_services[service_id]['worker_id']
            worker = next((w for w in self.workers if w['id'] == worker_id), None)
            
            if worker:
                # Remove the job from worker's current jobs
                worker['current_jobs'] = [
                    job for job in worker['current_jobs'] 
                    if job['service_id'] != service_id
                ]
                
                # Recalculate workload
                worker['current_workload'] = sum(job['duration'] for job in worker['current_jobs'])
                
                # Remove from active services
                del self.active_services[service_id]
                
                self.save_workload()
                print(f"✅ Completed service {service_id}, removed from {worker['name']}")
                
                # Process queue after completing a service
                self.process_queue()
                return True
        
        # Also check if service is in queue
        queue_item = next((item for item in self.service_queue if item['service_id'] == service_id), None)
        if queue_item:
            self.service_queue.remove(queue_item)
            self.save_workload()
            print(f"✅ Removed queued service {service_id}")
            return True
        
        return False
    
    def get_workload_data(self):
        """Get current workload data for all workers"""
        if not self.workers:
            self.initialize_default_workers()
            
        workload_data = []
        total_concurrent_jobs = 0
        
        for worker in self.workers:
            # Ensure worker has all required fields
            if 'max_concurrent_jobs' not in worker:
                worker['max_concurrent_jobs'] = 3
            
            workload_percentage = (worker['current_workload'] / worker['total_capacity']) * 100
            total_concurrent_jobs += len(worker['current_jobs'])
            
            # Determine status
            if workload_percentage < 40:
                status = 'low'
                status_text = 'Available'
            elif workload_percentage < 70:
                status = 'medium'
                status_text = 'Moderate'
            else:
                status = 'high'
                status_text = 'Busy'
            
            workload_data.append({
                'id': worker['id'],
                'name': worker['name'],
                'specialization': worker.get('specialization', 'General Maintenance'),
                'workload_percentage': round(workload_percentage, 1),
                'current_jobs': len(worker['current_jobs']),
                'max_jobs': worker['max_concurrent_jobs'],
                'current_workload': round(worker['current_workload'], 2),
                'total_capacity': worker['total_capacity'],
                'efficiency': worker.get('efficiency', 1.0),
                'rating': worker.get('rating', 4.5),
                'status': status,
                'status_text': status_text,
                'jobs_list': [f"{job['car_model']} ({job['service_type']})" for job in worker['current_jobs']]
            })
        
        total_capacity = sum(w['total_capacity'] for w in self.workers)
        utilized_capacity = sum(w['current_workload'] for w in self.workers)
        capacity_utilization = (utilized_capacity / total_capacity * 100) if total_capacity > 0 else 0
        
        return {
            'workers': workload_data,
            'summary': {
                'total_workers': len(self.workers),
                'total_active_jobs': total_concurrent_jobs,
                'available_workers': len(self.get_available_workers()),
                'queued_services': len(self.service_queue),
                'total_capacity': total_capacity,
                'utilized_capacity': utilized_capacity,
                'total_capacity_utilization': round(capacity_utilization, 1)
            }
        }
    
    def get_queue_info(self):
        """Get queue and worker availability information"""
        workload_data = self.get_workload_data()
        available_workers = len(self.get_available_workers())
        
        return {
            'total_active_jobs': workload_data['summary']['total_active_jobs'],
            'available_workers': available_workers,
            'busy_workers': len(self.workers) - available_workers,
            'total_workers': len(self.workers),
            'queued_services': len(self.service_queue),
            'average_workload': workload_data['summary']['utilized_capacity'] / len(self.workers) if self.workers else 0,
            'total_capacity_utilization': workload_data['summary']['total_capacity_utilization']
        }
    
    def get_active_services_count(self):
        """Get the actual count of active services"""
        return len(self.active_services)
    
    def get_all_active_services(self):
        """Get all active services data"""
        return self.active_services
    
    def reset_all(self):
        """Reset all workload data"""
        self.workers = []
        self.active_services = {}
        self.service_queue = []
        self.initialize_default_workers()
        self.save_workload()
        print("🔄 Reset all workload data")