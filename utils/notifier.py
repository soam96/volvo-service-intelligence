from flask_mail import Message
from datetime import datetime

class Notifier:
    def __init__(self, mail, app):
        self.mail = mail
        self.app = app
        self.sent_alerts = []
    
    def send_low_stock_alert(self, part_name, quantity):
        """Send email alert for low stock"""
        try:
            with self.app.app_context():
                msg = Message(
                    subject=f"⚠️ Low Stock Alert for {part_name}",
                    recipients=['admin@volvodealer.com', 'manager@volvodealer.com'],  # Replace with actual emails
                    sender='vsis@volvodealer.com',
                    body=f"""Dear Volvo Service Team,

CRITICAL INVENTORY ALERT

Part Name: {part_name}
Current Quantity: {quantity}
Alert Level: CRITICAL

The inventory for {part_name} is critically low. Please restock immediately to ensure uninterrupted service operations.

Recommended Action:
1. Order new stock immediately
2. Check with suppliers for quick delivery
3. Update inventory once restocked

This is an automated alert from the Volvo Service Intelligence System.

Best regards,
Volvo Service Intelligence System (VSIS)
                """
                )
                
                # Add HTML version
                msg.html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; }}
                        .alert {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 5px; }}
                        .critical {{ color: #dc3545; font-weight: bold; }}
                        .info {{ color: #856404; }}
                    </style>
                </head>
                <body>
                    <div class="alert">
                        <h2 class="critical">⚠️ Low Stock Alert</h2>
                        <p><strong>Part Name:</strong> {part_name}</p>
                        <p><strong>Current Quantity:</strong> {quantity}</p>
                        <p><strong>Status:</strong> <span class="critical">CRITICAL</span></p>
                        <p class="info">Please restock immediately to ensure uninterrupted service operations.</p>
                        <hr>
                        <p><small>This is an automated alert from Volvo Service Intelligence System (VSIS)<br>
                        Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
                    </div>
                </body>
                </html>
                """
                
                # In production, uncomment the line below to actually send emails
                # self.mail.send(msg)
                
                # Store alert record
                alert_record = {
                    'part_name': part_name,
                    'quantity': quantity,
                    'timestamp': datetime.now().isoformat(),
                    'type': 'low_stock',
                    'sent': True  # In demo, mark as sent but don't actually send
                }
                self.sent_alerts.append(alert_record)
                
                # Keep only last 50 alerts
                if len(self.sent_alerts) > 50:
                    self.sent_alerts = self.sent_alerts[-50:]
                
                print(f"📧 Low stock alert prepared for {part_name} (Quantity: {quantity})")
                return True
                
        except Exception as e:
            print(f"❌ Failed to send email alert: {e}")
            return False
    
    def send_service_completion_alert(self, service_data):
        """Send email notification when service is completed"""
        try:
            with self.app.app_context():
                msg = Message(
                    subject=f"✅ Service Completed - {service_data['service_id']}",
                    recipients=['customer@example.com'],  # Would be actual customer email
                    sender='vsis@volvodealer.com',
                    body=f"""Dear Customer,

Your Volvo service has been completed successfully!

Service Details:
- Service ID: {service_data['service_id']}
- Vehicle: {service_data['car_details']['car_model']}
- Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Total Service Time: {service_data['predicted_time']} hours

Your vehicle is ready for pickup. Thank you for choosing Volvo Service!

Best regards,
Volvo Service Center
                """
                )
                
                # In production, uncomment below
                # self.mail.send(msg)
                
                print(f"📧 Service completion alert prepared for {service_data['service_id']}")
                return True
                
        except Exception as e:
            print(f"❌ Failed to send completion alert: {e}")
            return False
    
    def get_recent_alerts(self, limit=10):
        """Get recent email alerts"""
        return self.sent_alerts[-limit:] if self.sent_alerts else []
