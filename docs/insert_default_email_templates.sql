-- Insert default email templates with SchoolId = NULL (for all schools)

-- Check if default ADMISSION_ACKNOWLEDGMENT exists
IF NOT EXISTS (SELECT 1 FROM EmailTemplate WHERE Code = 'ADMISSION_ACKNOWLEDGMENT' AND SchoolId IS NULL)
BEGIN
    INSERT INTO EmailTemplate (Code, SchoolId, Language, SubjectTemplate, BodyTextTemplate, BodyHtmlTemplate, IsActive, CreatedAt, UpdatedAt)
    VALUES (
        'ADMISSION_ACKNOWLEDGMENT',
        NULL,
        'en',
        '🎉 Welcome to {{ school_name }} - Admission Confirmed!',
        'Dear {{ student_name }}, Congratulations! Your admission to {{ school_name }} has been confirmed. Student Code: {{ student_code }}, Class: {{ admission_class }}, Admission Date: {{ admission_date }}. Best regards, {{ school_name }}',
        '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"></head><body style="margin:0;padding:0;background:#f4f7fa;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif"><table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f7fa;padding:20px 0"><tr><td align="center"><table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.1)"><tr><td style="background:linear-gradient(135deg,#10b981,#059669);padding:30px 20px;text-align:center"><h1 style="margin:0;color:#fff;font-size:28px;font-weight:600">🎉 Admission Confirmed!</h1></td></tr><tr><td style="padding:30px 20px"><p style="margin:0 0 20px;font-size:16px;color:#333;line-height:1.6">Dear <strong>{{ student_name }}</strong>,</p><p style="margin:0 0 20px;font-size:16px;color:#555;line-height:1.6">Congratulations! We are delighted to confirm your admission to <strong style="color:#10b981">{{ school_name }}</strong>.</p><table width="100%" cellpadding="0" cellspacing="0" style="background:#f0fdf4;border-left:4px solid #10b981;border-radius:8px;margin:20px 0"><tr><td style="padding:20px"><h3 style="margin:0 0 15px;color:#059669;font-size:18px">📋 Student Details</h3><table width="100%" cellpadding="8" cellspacing="0"><tr><td style="color:#666;font-size:14px;padding:8px 0"><strong>Name:</strong></td><td style="color:#333;font-size:14px;padding:8px 0;text-align:right">{{ student_name }}</td></tr><tr><td style="color:#666;font-size:14px;padding:8px 0"><strong>Student Code:</strong></td><td style="color:#333;font-size:14px;padding:8px 0;text-align:right"><span style="background:#10b981;color:#fff;padding:4px 12px;border-radius:20px;font-weight:600">{{ student_code }}</span></td></tr><tr><td style="color:#666;font-size:14px;padding:8px 0"><strong>Class:</strong></td><td style="color:#333;font-size:14px;padding:8px 0;text-align:right">{{ admission_class }}</td></tr><tr><td style="color:#666;font-size:14px;padding:8px 0"><strong>Admission Date:</strong></td><td style="color:#333;font-size:14px;padding:8px 0;text-align:right">{{ admission_date }}</td></tr></table></td></tr></table><p style="margin:20px 0;font-size:14px;color:#555;line-height:1.6">📎 Please find your admission acknowledgment document attached to this email.</p><p style="margin:20px 0 0;font-size:14px;color:#333;line-height:1.6">Best regards,<br><strong style="color:#10b981">{{ school_name }}</strong></p></td></tr><tr><td style="background:#f9fafb;padding:20px;text-align:center;border-top:1px solid #e5e7eb"><p style="margin:0;font-size:12px;color:#6b7280">This is an automated email. Please do not reply.</p></td></tr></table></td></tr></table></body></html>',
        0,
        GETDATE(),
        GETDATE()
    );
    PRINT 'Default ADMISSION_ACKNOWLEDGMENT template inserted';
END

-- Check if default PAYMENT_RECEIPT exists
IF NOT EXISTS (SELECT 1 FROM EmailTemplate WHERE Code = 'PAYMENT_RECEIPT' AND SchoolId IS NULL)
BEGIN
    INSERT INTO EmailTemplate (Code, SchoolId, Language, SubjectTemplate, BodyTextTemplate, BodyHtmlTemplate, IsActive, CreatedAt, UpdatedAt)
    VALUES (
        'PAYMENT_RECEIPT',
        NULL,
        'en',
        '✅ Payment Received - Receipt #{{ receipt_number }}',
        'Dear {{ student_name }}, Thank you for your payment. Receipt Number: {{ receipt_number }}, Amount Paid: Rs.{{ amount_paid }}, Payment Mode: {{ payment_mode }}, Payment Date: {{ payment_date }}. Best regards, {{ school_name }}',
        '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"></head><body style="margin:0;padding:0;background:#f4f7fa;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif"><table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f7fa;padding:20px 0"><tr><td align="center"><table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.1)"><tr><td style="background:linear-gradient(135deg,#4f46e5,#4338ca);padding:30px 20px;text-align:center"><h1 style="margin:0;color:#fff;font-size:28px;font-weight:600">✅ Payment Received</h1></td></tr><tr><td style="padding:30px 20px"><p style="margin:0 0 20px;font-size:16px;color:#333;line-height:1.6">Dear <strong>{{ student_name }}</strong>,</p><p style="margin:0 0 20px;font-size:16px;color:#555;line-height:1.6">Thank you for your payment. Your transaction has been successfully processed.</p><table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4ff;border-left:4px solid #4f46e5;border-radius:8px;margin:20px 0"><tr><td style="padding:20px"><h3 style="margin:0 0 15px;color:#4338ca;font-size:18px">💳 Payment Details</h3><table width="100%" cellpadding="8" cellspacing="0"><tr><td style="color:#666;font-size:14px;padding:8px 0"><strong>Receipt Number:</strong></td><td style="color:#333;font-size:14px;padding:8px 0;text-align:right"><span style="background:#4f46e5;color:#fff;padding:4px 12px;border-radius:20px;font-weight:600">{{ receipt_number }}</span></td></tr><tr><td style="color:#666;font-size:14px;padding:8px 0"><strong>Amount Paid:</strong></td><td style="color:#10b981;font-size:18px;font-weight:700;padding:8px 0;text-align:right">₹{{ amount_paid }}</td></tr><tr><td style="color:#666;font-size:14px;padding:8px 0"><strong>Payment Mode:</strong></td><td style="color:#333;font-size:14px;padding:8px 0;text-align:right">{{ payment_mode }}</td></tr><tr><td style="color:#666;font-size:14px;padding:8px 0"><strong>Payment Date:</strong></td><td style="color:#333;font-size:14px;padding:8px 0;text-align:right">{{ payment_date }}</td></tr><tr><td style="color:#666;font-size:14px;padding:8px 0"><strong>Student Code:</strong></td><td style="color:#333;font-size:14px;padding:8px 0;text-align:right">{{ student_code }}</td></tr></table></td></tr></table><p style="margin:20px 0;font-size:14px;color:#555;line-height:1.6">📎 Your payment receipt is attached to this email for your records.</p><p style="margin:20px 0 0;font-size:14px;color:#333;line-height:1.6">Best regards,<br><strong style="color:#4f46e5">{{ school_name }}</strong></p></td></tr><tr><td style="background:#f9fafb;padding:20px;text-align:center;border-top:1px solid #e5e7eb"><p style="margin:0;font-size:12px;color:#6b7280">This is an automated email. Please do not reply.</p></td></tr></table></td></tr></table></body></html>',
        0,
        GETDATE(),
        GETDATE()
    );
    PRINT 'Default PAYMENT_RECEIPT template inserted';
END

PRINT 'Default email templates setup completed';
