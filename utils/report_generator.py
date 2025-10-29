from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

class ReportGenerator:
    def __init__(self):
        self.reports_dir = 'reports'
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
        
        # Register fonts (you would need actual font files)
        try:
            # pdfmetrics.registerFont(TTFont('Poppins', 'Poppins-Regular.ttf'))
            pass
        except:
            print("⚠️ Using default fonts for PDF generation")
    
    def generate_service_report(self, service_data):
        """Generate PDF service report"""
        filename = f"{self.reports_dir}/{service_data['service_id']}_report.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Center
            textColor=colors.HexColor('#1C2541')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#3A86FF')
        )
        
        # Header with Volvo branding
        header_table = Table([
            [Paragraph("VOLVO SERVICE INTELLIGENCE SYSTEM", title_style)],
            [Paragraph("Service Report", styles['Heading2'])],
            [Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])]
        ], colWidths=[7*inch])
        
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 20))
        
        # Service Information
        service_info = [
            ['Service ID:', service_data['service_id']],
            ['Report Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Car Model:', service_data['car_details']['car_model']],
            ['Number Plate:', service_data['car_details']['number_plate']],
            ['Manufacture Year:', service_data['car_details']['manufacture_year']],
            ['Fuel Type:', service_data['car_details']['fuel_type']],
            ['Service Type:', service_data['car_details']['service_type']]
        ]
        
        service_table = Table(service_info, colWidths=[2*inch, 4*inch])
        service_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1C2541')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
        ]))
        
        story.append(Paragraph("Service Information", heading_style))
        story.append(service_table)
        story.append(Spacer(1, 20))
        
        # Service Details
        completion_time = datetime.fromisoformat(service_data['completion_time'])
        service_details = [
            ['Predicted Service Time:', f"{service_data['predicted_time']} hours"],
            ['Worker Assigned:', service_data['worker_assigned']['worker_name']],
            ['Worker Specialization:', service_data['worker_assigned']['specialization']],
            ['Estimated Completion:', completion_time.strftime('%Y-%m-%d %H:%M')],
            ['Workload Level:', f"{service_data['worker_assigned']['workload_percentage']:.1f}%"],
            ['Parts Availability:', '✅ All Parts Available' if service_data['inventory_status']['available'] else '❌ Some Parts Unavailable']
        ]
        
        details_table = Table(service_details, colWidths=[2.5*inch, 3.5*inch])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3A86FF')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E8F4FD')),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ]))
        
        story.append(Paragraph("Service Details", heading_style))
        story.append(details_table)
        story.append(Spacer(1, 20))
        
        # Selected Tasks
        if 'selected_tasks' in service_data['car_details']:
            story.append(Paragraph("Performed Tasks", heading_style))
            tasks = service_data['car_details']['selected_tasks']
            if tasks:
                task_data = [[Paragraph("Task Name", styles['Normal'])]]
                for task in tasks:
                    task_data.append([Paragraph(task.replace('_', ' ').title(), styles['Normal'])])
                
                tasks_table = Table(task_data, colWidths=[6*inch])
                tasks_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#06D6A0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F0FDF4')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ]))
                story.append(tasks_table)
            else:
                story.append(Paragraph("No specific tasks selected", styles['Normal']))
            
            story.append(Spacer(1, 20))
        
        # Parts Used
        if 'required_parts' in service_data['inventory_status']:
            story.append(Paragraph("Parts Utilization", heading_style))
            parts_data = [[Paragraph("Part Name", styles['Normal']), Paragraph("Quantity Used", styles['Normal'])]]
            
            for part_id, quantity in service_data['inventory_status']['required_parts'].items():
                parts_data.append([
                    Paragraph(part_id.replace('_', ' ').title(), styles['Normal']),
                    Paragraph(str(quantity), styles['Normal'])
                ])
            
            parts_table = Table(parts_data, colWidths=[4*inch, 2*inch])
            parts_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFD166')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFFBEB')),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ]))
            story.append(parts_table)
            story.append(Spacer(1, 20))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1
        )
        
        footer = Paragraph(
            "Generated by Volvo Service Intelligence System (VSIS) | "
            "Confidential Service Report | "
            f"Page 1 of 1",
            footer_style
        )
        
        story.append(Spacer(1, 40))
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        print(f"📄 PDF report generated: {filename}")
        return filename