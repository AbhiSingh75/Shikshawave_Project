-- Create/Update LOGIN_OTP Email Template (Global Template)
-- This template is used for sending OTP during login
-- Global template means SchoolId = NULL, so it works for all schools

-- Delete existing template if it exists
IF EXISTS (SELECT 1 FROM EmailTemplate WHERE Code = 'LOGIN_OTP' AND SchoolId IS NULL)
BEGIN
    DELETE FROM EmailTemplate WHERE Code = 'LOGIN_OTP' AND SchoolId IS NULL;
    PRINT 'Existing LOGIN_OTP template deleted';
END

-- Insert new global template
INSERT INTO EmailTemplate (
    Code,
    SchoolId,
    Language,
    SubjectTemplate,
    BodyTextTemplate,
    BodyHtmlTemplate,
    DefaultFrom,
    Cc,
    Bcc,
    Placeholders,
    IsActive,
    CreatedAt,
    UpdatedAt
)
VALUES (
    'LOGIN_OTP',
    NULL,  -- NULL = Global template for all schools
    'en',
    'ShikshaWave - Your Login OTP Code',
    'Hello {{ user_name }},

Your One-Time Password (OTP) for login is: {{ otp }}

This OTP is valid for {{ valid_minutes }} minutes.

Login attempt from IP: {{ ip_address }}

If you did not request this OTP, please ignore this email or contact support immediately.

Best regards,
ShikshaWave Team',
    '<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShikshaWave Login OTP</title>
</head>
<body style="margin: 0; padding: 0; font-family: ''Segoe UI'', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f4f7fa; padding: 40px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600; letter-spacing: 0.5px;">🔐 ShikshaWave</h1>
                            <p style="margin: 10px 0 0 0; color: #e0e7ff; font-size: 16px;">Secure Login Verification</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="margin: 0 0 20px 0; color: #333333; font-size: 16px; line-height: 1.6;">
                                Hello <strong style="color: #667eea;">{{ user_name }}</strong>,
                            </p>
                            
                            <p style="margin: 0 0 30px 0; color: #555555; font-size: 15px; line-height: 1.6;">
                                We received a request to log in to your ShikshaWave account. Use the following One-Time Password (OTP) to complete your login:
                            </p>
                            
                            <!-- OTP Box -->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; padding: 25px; display: inline-block;">
                                            <div style="background-color: #ffffff; border-radius: 8px; padding: 20px 40px; display: inline-block;">
                                                <span style="font-size: 42px; font-weight: bold; color: #667eea; letter-spacing: 8px; font-family: ''Courier New'', monospace;">{{ otp }}</span>
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Info Box -->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 30px 0; background-color: #fff8e1; border-left: 4px solid #ffc107; border-radius: 6px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="margin: 0; color: #856404; font-size: 14px; line-height: 1.6;">
                                            <strong>⏱️ Important:</strong> This OTP is valid for <strong>{{ valid_minutes }} minutes</strong> only. Do not share this code with anyone.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Login Details -->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 25px 0; background-color: #f8f9fa; border-radius: 6px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="margin: 0 0 10px 0; color: #333333; font-size: 14px; font-weight: 600;">📍 Login Details:</p>
                                        <p style="margin: 5px 0; color: #666666; font-size: 13px;">• IP Address: <strong>{{ ip_address }}</strong></p>
                                        <p style="margin: 5px 0; color: #666666; font-size: 13px;">• Time: <strong>Just now</strong></p>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Security Notice -->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 25px 0; background-color: #fff3f3; border-left: 4px solid #dc3545; border-radius: 6px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="margin: 0; color: #721c24; font-size: 13px; line-height: 1.6;">
                                            <strong>🛡️ Security Alert:</strong> If you did not request this OTP, please ignore this email and contact our support team immediately. Your account security is important to us.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 30px 0 0 0; color: #555555; font-size: 14px; line-height: 1.6;">
                                Best regards,<br>
                                <strong style="color: #667eea;">ShikshaWave Team</strong>
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8f9fa; padding: 30px; text-align: center; border-top: 1px solid #e9ecef;">
                            <p style="margin: 0 0 10px 0; color: #6c757d; font-size: 12px;">
                                © 2024 ShikshaWave. All rights reserved.
                            </p>
                            <p style="margin: 0; color: #6c757d; font-size: 11px;">
                                This is an automated email. Please do not reply to this message.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>',
    'ShikshaWave <shikshawaves@gmail.com>',
    NULL,
    NULL,
    '{"user_name": "User full name", "otp": "6-digit OTP code", "valid_minutes": "OTP validity in minutes", "ip_address": "Login IP address"}',
    1,  -- IsActive = 1 (Active)
    GETDATE(),
    GETDATE()
);

PRINT 'LOGIN_OTP global email template created successfully';
PRINT 'Template Code: LOGIN_OTP';
PRINT 'SchoolId: NULL (Global template for all schools)';
PRINT 'Status: Active';
GO
