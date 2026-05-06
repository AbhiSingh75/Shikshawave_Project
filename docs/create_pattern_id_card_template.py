#!/usr/bin/env python3
"""
Fresh Script to Create Pattern Background ID Card Template
This script creates a new template that exactly matches the reference design.
"""

def create_pattern_id_card_template():
    """Create a fresh ID card template with pattern background"""
    
    template_content = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        .id-card {
            width: 240px;
            height: 400px;
            background: #f8fafc;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            margin: 0 auto;
            overflow: hidden;
            border: 2px solid #e2e8f0;
            font-family: 'Arial', sans-serif;
            position: relative;
        }
        
        /* Pattern Background */
        .pattern-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: 
                radial-gradient(circle at 20% 20%, rgba(59, 130, 246, 0.04) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(59, 130, 246, 0.04) 0%, transparent 50%),
                radial-gradient(circle at 40% 60%, rgba(59, 130, 246, 0.02) 0%, transparent 50%);
            background-size: 80px 80px, 100px 100px, 60px 60px;
            background-position: 0 0, 40px 40px, 20px 20px;
        }
        
        /* Logo Section */
        .logo-area {
            text-align: center;
            padding: 20px 0 15px;
            position: relative;
            z-index: 10;
        }
        
        .school-logo {
            width: 50px;
            height: 50px;
            object-fit: contain;
            border-radius: 8px;
        }
        
        .logo-fallback {
            width: 50px;
            height: 50px;
            background: #dc2626;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
        }
        
        /* School Information */
        .school-title {
            font-size: 20px;
            font-weight: 700;
            color: #1e293b;
            text-align: center;
            margin: 15px 15px 10px;
            line-height: 1.1;
            position: relative;
            z-index: 10;
        }
        
        .school-tagline {
            font-size: 11px;
            color: #64748b;
            text-align: center;
            margin: 0 15px 25px;
            line-height: 1.3;
            position: relative;
            z-index: 10;
        }
        
        /* Student Photo */
        .photo-container {
            text-align: center;
            margin-bottom: 20px;
            position: relative;
            z-index: 10;
        }
        
        .student-photo {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            object-fit: cover;
            border: 4px solid white;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .photo-fallback {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: linear-gradient(135deg, #1e293b, #334155);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 40px;
            border: 4px solid white;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        /* Barcode */
        .barcode-area {
            text-align: center;
            margin-bottom: 15px;
            position: relative;
            z-index: 10;
        }
        
        .barcode {
            width: 120px;
            height: 30px;
            background: repeating-linear-gradient(
                90deg,
                #1e293b 0px,
                #1e293b 2px,
                transparent 2px,
                transparent 4px,
                #1e293b 4px,
                #1e293b 6px,
                transparent 6px,
                transparent 8px
            );
            margin: 0 auto;
        }
        
        /* Student Name */
        .student-name {
            font-size: 16px;
            font-weight: 700;
            color: #1e293b;
            text-align: center;
            margin-bottom: 25px;
            letter-spacing: 1px;
            position: relative;
            z-index: 10;
        }
        
        /* Bottom Section */
        .bottom-section {
            padding: 0 20px 20px;
            position: relative;
            z-index: 10;
        }
        
        .student-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 700;
            color: #1e293b;
            text-decoration: underline;
            margin-bottom: 15px;
        }
        
        .info-container {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }
        
        .info-list {
            font-size: 12px;
            color: #1e293b;
            font-weight: 500;
        }
        
        .info-item {
            margin-bottom: 8px;
        }
        
        .qr-placeholder {
            width: 50px;
            height: 50px;
            background: white;
            border: 2px solid #1e293b;
            border-radius: 8px;
            position: relative;
        }
        
        .qr-corner {
            position: absolute;
            width: 8px;
            height: 8px;
            border: 2px solid #1e293b;
        }
        
        .qr-corner.tl { top: 4px; left: 4px; }
        .qr-corner.tr { top: 4px; right: 4px; }
        .qr-corner.bl { bottom: 4px; left: 4px; }
        .qr-corner.br { bottom: 4px; right: 4px; }
    </style>
</head>
<body style="margin:0;padding:0;font-family:Arial,sans-serif;">
    <div class="id-card">
        <!-- Pattern Background -->
        <div class="pattern-overlay"></div>
        
        <!-- Logo Section -->
        <div class="logo-area">
            {% if student.SchoolLogoBase64 %}
                <img src="data:image/png;base64,{{ student.SchoolLogoBase64 }}" class="school-logo" alt="School Logo">
            {% else %}
                <div class="logo-fallback">
                    <i class="fas fa-graduation-cap"></i>
                </div>
            {% endif %}
        </div>
        
        <!-- School Information -->
        <div class="school-title">{{ student.SchoolName|default:"School Name" }}</div>
        <div class="school-tagline">
            Growing Together, Learning Forever –<br>
            {{ student.SchoolName|default:"School Name" }}
        </div>
        
        <!-- Student Photo -->
        <div class="photo-container">
            {% if student.PhotoBase64 %}
                <img src="data:image/png;base64,{{ student.PhotoBase64 }}" class="student-photo" alt="{{ student.FullName }}">
            {% else %}
                <div class="photo-fallback">
                    {{ student.FullName|first|upper }}
                </div>
            {% endif %}
        </div>
        
        <!-- Barcode -->
        <div class="barcode-area">
            <div class="barcode"></div>
        </div>
        
        <!-- Student Name -->
        <div class="student-name">{{ student.FullName|upper }}</div>
        
        <!-- Bottom Section -->
        <div class="bottom-section">
            <div class="student-badge">
                <i class="fas fa-graduation-cap"></i>
                STUDENT
            </div>
            
            <div class="info-container">
                <div class="info-list">
                    <div class="info-item">ID → {{ student.StudentCode }}</div>
                    <div class="info-item">Class → {{ student.ClassName }}</div>
                    <div class="info-item">DOA → {{ student.DateOfBirth|date:"d M Y"|default:"01 Apr 2025" }}</div>
                </div>
                
                <div class="qr-placeholder">
                    <div class="qr-corner tl"></div>
                    <div class="qr-corner tr"></div>
                    <div class="qr-corner bl"></div>
                    <div class="qr-corner br"></div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
    
    return template_content

def save_template():
    """Save the template to the correct location"""
    import os
    
    template_content = create_pattern_id_card_template()
    
    # Template file path
    template_path = "core/templates/core/document_templates/student_id_card/student_card_vertical_14.html"
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(template_path), exist_ok=True)
    
    # Write template file
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print(f"✅ Template created: {template_path}")
    print("📋 Template Features:")
    print("   - Pattern background with subtle gradients")
    print("   - Clean logo section")
    print("   - Professional typography")
    print("   - Circular student photo with shadow")
    print("   - CSS-generated barcode")
    print("   - Student badge with icon")
    print("   - Info section with QR placeholder")
    print("   - Exact layout matching reference design")

if __name__ == "__main__":
    save_template()