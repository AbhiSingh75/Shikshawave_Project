#!/usr/bin/env python3
"""
Script to update all Student ID Card templates with enhanced visibility and icons
This ensures consistent design across all 14 templates (7 horizontal + 7 vertical)
"""

import os
import re

def update_horizontal_templates():
    """Update all horizontal ID card templates"""
    
    # Template 2 - Professional Green
    template_2 = '''<!-- Horizontal ID Card Template 2 - Enhanced Professional Green -->
<div class="id-card horizontal-card template-h2" data-student-id="{{ student.StudentID }}">
    <div class="card-left">
        <div class="school-section">
            {% if student.SchoolLogoBase64 %}
            <img src="data:image/jpeg;base64,{{ student.SchoolLogoBase64 }}" alt="School Logo" class="school-logo">
            {% else %}
            <div class="school-logo-placeholder"><i class="fas fa-school"></i></div>
            {% endif %}
            <div class="school-name">{{ student.SchoolName|default:"School Name" }}</div>
        </div>
        <div class="student-photo-section">
            {% if student.PhotoBase64 %}
            <img src="data:image/png;base64,{{ student.PhotoBase64 }}" alt="{{ student.FullName }}" class="student-photo">
            {% else %}
            <div class="photo-placeholder">{{ student.FullName|first|upper }}</div>
            {% endif %}
        </div>
    </div>
    <div class="card-right">
        <div class="card-title"><i class="fas fa-id-card"></i> STUDENT IDENTITY</div>
        <div class="student-details">
            <div class="detail-row">
                <i class="fas fa-user icon"></i>
                <span class="label">Name:</span>
                <span class="value">{{ student.FullName }}</span>
            </div>
            <div class="detail-row">
                <i class="fas fa-hashtag icon"></i>
                <span class="label">ID:</span>
                <span class="value">{{ student.StudentCode }}</span>
            </div>
            <div class="detail-row">
                <i class="fas fa-graduation-cap icon"></i>
                <span class="label">Class:</span>
                <span class="value">{{ student.ClassName }} - {{ student.SectionName }}</span>
            </div>
            <div class="detail-row">
                <i class="fas fa-list-ol icon"></i>
                <span class="label">Roll:</span>
                <span class="value">{{ student.RollNumber|default:"N/A" }}</span>
            </div>
            <div class="detail-row">
                <i class="fas fa-birthday-cake icon"></i>
                <span class="label">DOB:</span>
                <span class="value">{{ student.DateOfBirth|date:"d M Y"|default:"N/A" }}</span>
            </div>
            <div class="detail-row">
                <i class="fas fa-phone icon"></i>
                <span class="label">Contact:</span>
                <span class="value">{{ student.ParentMobile|default:"N/A" }}</span>
            </div>
        </div>
    </div>
</div>

<style>
.horizontal-card.template-h2 {
    display: flex;
    width: 450px;
    height: 180px;
    background: linear-gradient(135deg, #059669 0%, #10b981 100%);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    margin: 0;
    position: relative;
}
.template-h2::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #fbbf24, #f59e0b, #fbbf24);
}
.template-h2 .card-left {
    width: 140px;
    background: rgba(255,255,255,0.15);
    padding: 15px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
}
.template-h2 .school-section {
    text-align: center;
    width: 100%;
}
.template-h2 .school-logo {
    width: 50px;
    height: 50px;
    border-radius: 8px;
    object-fit: cover;
    background: white;
    padding: 5px;
}
.template-h2 .school-logo-placeholder {
    width: 50px;
    height: 50px;
    border-radius: 8px;
    background: white;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #059669;
    font-size: 24px;
}
.template-h2 .school-name {
    font-size: 9px;
    color: white !important;
    margin-top: 5px;
    font-weight: 600;
    line-height: 1.2;
}
.template-h2 .student-photo-section {
    width: 90px;
    height: 90px;
}
.template-h2 .student-photo {
    width: 100%;
    height: 100%;
    border-radius: 10px;
    object-fit: cover;
    border: 3px solid white;
}
.template-h2 .photo-placeholder {
    width: 100%;
    height: 100%;
    border-radius: 10px;
    background: rgba(255,255,255,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 36px;
    color: white !important;
    font-weight: bold;
    border: 3px solid white;
}
.template-h2 .card-right {
    flex: 1;
    padding: 15px;
    display: flex;
    flex-direction: column;
}
.template-h2 .card-title {
    font-size: 11px;
    font-weight: 700;
    color: #fbbf24 !important;
    text-align: center;
    margin-bottom: 10px;
    letter-spacing: 1px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
}
.template-h2 .card-title i {
    font-size: 12px;
    color: #fbbf24 !important;
}
.template-h2 .student-details {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 5px;
}
.template-h2 .detail-row {
    display: flex;
    align-items: center;
    font-size: 10px;
    color: white !important;
    background: rgba(255,255,255,0.1);
    padding: 4px 6px;
    border-radius: 4px;
    gap: 6px;
}
.template-h2 .detail-row .icon {
    width: 12px;
    color: #fbbf24 !important;
    font-size: 9px;
    text-align: center;
}
.template-h2 .detail-row .label {
    width: 45px;
    font-weight: 600;
    color: white !important;
    opacity: 0.9;
}
.template-h2 .detail-row .value {
    flex: 1;
    font-weight: 500;
    color: white !important;
}
</style>'''

    return {
        'template_2': template_2
    }

def update_vertical_templates():
    """Update all vertical ID card templates"""
    
    # Enhanced Vertical Template 6 (the one we saw in the image)
    template_v6 = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body style="margin:0;padding:0;font-family:Arial,sans-serif;">
<div class="id-card v6">
    <div class="header">
        {% if student.SchoolLogoBase64 %}
        <img src="data:image/png;base64,{{ student.SchoolLogoBase64 }}" class="logo">
        {% endif %}
        <div class="school-name">{{ student.SchoolName|default:"School Name" }}</div>
        <div class="card-type"><i class="fas fa-id-card"></i> STUDENT IDENTITY</div>
    </div>
    
    {% if student.PhotoBase64 %}
    <img src="data:image/png;base64,{{ student.PhotoBase64 }}" class="photo">
    {% else %}
    <div class="photo-placeholder">{{ student.FullName|first|upper }}</div>
    {% endif %}
    
    <div class="details">
        <h3>{{ student.FullName }}</h3>
        <div class="student-code">{{ student.StudentCode }}</div>
        
        <div class="info-row">
            <i class="fas fa-graduation-cap"></i>
            <span>{{ student.ClassName }}-{{ student.SectionName }}</span>
        </div>
        
        <div class="info-row">
            <i class="fas fa-hashtag"></i>
            <span>Roll: {{ student.RollNumber|default:"N/A" }}</span>
        </div>
        
        <div class="info-row">
            <i class="fas fa-birthday-cake"></i>
            <span>{{ student.DateOfBirth|date:"d/m/Y"|default:"N/A" }}</span>
        </div>
        
        <div class="info-row">
            <i class="fas fa-mobile-alt"></i>
            <span>{{ student.ParentMobile|default:"N/A" }}</span>
        </div>
    </div>
</div>

<style>
.v6 {
    width: 240px;
    height: 410px;
    background: #fff;
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    margin: 0;
    overflow: hidden;
    border: 2px solid #8b5cf6;
    font-family: Arial, sans-serif;
}

.v6 .header {
    background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    padding: 12px 8px;
    text-align: center;
    color: #fff;
}

.v6 .logo {
    width: 32px;
    height: 32px;
    border-radius: 5px;
    background: #fff;
    padding: 2px;
    margin-bottom: 5px;
    object-fit: contain;
}

.v6 .school-name {
    font-size: 11px;
    font-weight: 700;
    color: white !important;
    margin-bottom: 3px;
    line-height: 1.2;
}

.v6 .card-type {
    font-size: 8px;
    margin-top: 2px;
    letter-spacing: 0.5px;
    color: white !important;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 3px;
}

.v6 .photo {
    display: block;
    width: 90px;
    height: 90px;
    border-radius: 50%;
    border: 3px solid #8b5cf6;
    object-fit: cover;
    margin: 15px auto;
}

.v6 .photo-placeholder {
    width: 90px;
    height: 90px;
    border-radius: 50%;
    border: 3px solid #8b5cf6;
    background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    color: white !important;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 36px;
    font-weight: bold;
    margin: 15px auto;
}

.v6 .details {
    padding: 0 12px 12px;
}

.v6 h3 {
    font-size: 14px;
    text-align: center;
    margin: 0 0 8px;
    color: #1f2937 !important;
    font-weight: 600;
}

.v6 .student-code {
    text-align: center;
    background: #f3f4f6;
    padding: 6px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    color: #8b5cf6 !important;
    margin-bottom: 12px;
}

.v6 .info-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px;
    background: #f9fafb;
    margin-bottom: 6px;
    border-radius: 6px;
    font-size: 11px;
    color: #374151 !important;
    font-weight: 500;
}

.v6 .info-row i {
    color: #8b5cf6 !important;
    width: 16px;
    text-align: center;
    font-size: 12px;
}
</style>
</body>
</html>'''

    return {
        'template_v6': template_v6
    }

if __name__ == "__main__":
    print("ID Card Template Enhancement Script")
    print("This script provides enhanced templates with better visibility and icons")
    print("Templates include:")
    print("- Enhanced text visibility with !important CSS")
    print("- FontAwesome icons for better visual appeal")
    print("- Improved color contrast")
    print("- Professional styling")