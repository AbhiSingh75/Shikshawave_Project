-- Create Multiple OTP Email Templates (Pre-built Designs)
-- Users can select from these templates in Template Management

-- Delete existing LOGIN_OTP templates
DELETE FROM EmailTemplate WHERE Code = 'LOGIN_OTP';

-- Template 1: Modern Gradient (Default)
INSERT INTO EmailTemplate (Code, SchoolId, Language, SubjectTemplate, BodyTextTemplate, BodyHtmlTemplate, DefaultFrom, Cc, Bcc, Placeholders, IsActive, CreatedAt, UpdatedAt)
VALUES (
    'LOGIN_OTP',
    NULL,
    'en',
    '{% if school_name %}{{ school_name }} - {% endif %}Your Login OTP Code',
    'Hello {{ user_name }},

Your OTP: {{ otp }}
Valid for {{ valid_minutes }} minutes.
IP: {{ ip_address }}

{% if school_name %}{{ school_name }}{% else %}ShikshaWave{% endif %}',
    '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head><body style="margin:0;padding:0;font-family:Arial,sans-serif;background:#f4f7fa"><table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f7fa;padding:40px 0"><tr><td align="center"><table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.1)"><tr><td style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:40px 30px;text-align:center;border-radius:12px 12px 0 0"><h1 style="margin:0;color:#fff;font-size:28px">🔐 {% if school_name %}{{ school_name }}{% else %}ShikshaWave{% endif %}</h1><p style="margin:10px 0 0;color:#e0e7ff;font-size:16px">Secure Login Verification</p></td></tr><tr><td style="padding:40px 30px"><p style="margin:0 0 20px;color:#333;font-size:16px">Hello <strong style="color:#667eea">{{ user_name }}</strong>,</p><p style="margin:0 0 30px;color:#555;font-size:15px">Your One-Time Password:</p><table width="100%" cellpadding="0" cellspacing="0" style="margin:30px 0"><tr><td align="center"><div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:10px;padding:25px"><div style="background:#fff;border-radius:8px;padding:20px 40px"><span style="font-size:42px;font-weight:bold;color:#667eea;letter-spacing:8px;font-family:Courier New,monospace">{{ otp }}</span></div></div></td></tr></table><table width="100%" cellpadding="0" cellspacing="0" style="margin:30px 0;background:#fff8e1;border-left:4px solid #ffc107;border-radius:6px"><tr><td style="padding:20px"><p style="margin:0;color:#856404;font-size:14px">⏱️ Valid for <strong>{{ valid_minutes }} minutes</strong></p></td></tr></table><table width="100%" cellpadding="0" cellspacing="0" style="margin:25px 0;background:#f8f9fa;border-radius:6px"><tr><td style="padding:20px"><p style="margin:0 0 10px;color:#333;font-size:14px;font-weight:600">📍 Login Details:</p><p style="margin:5px 0;color:#666;font-size:13px">• IP: <strong>{{ ip_address }}</strong></p></td></tr></table></td></tr><tr><td style="background:#f8f9fa;padding:30px;text-align:center;border-top:1px solid #e9ecef;border-radius:0 0 12px 12px"><p style="margin:0;color:#6c757d;font-size:12px">© 2024 {% if school_name %}{{ school_name }}{% else %}ShikshaWave{% endif %}</p></td></tr></table></td></tr></table></body></html>',
    'ShikshaWave <shikshawaves@gmail.com>',
    NULL,
    NULL,
    '{"user_name":"User name","otp":"6-digit code","valid_minutes":"15","ip_address":"IP","school_name":"School name (optional)"}',
    1,
    GETDATE(),
    GETDATE()
);

-- Template 2: Minimal Clean
INSERT INTO EmailTemplate (Code, SchoolId, Language, SubjectTemplate, BodyTextTemplate, BodyHtmlTemplate, DefaultFrom, Cc, Bcc, Placeholders, IsActive, CreatedAt, UpdatedAt)
VALUES (
    'LOGIN_OTP_MINIMAL',
    NULL,
    'en',
    '{% if school_name %}{{ school_name }} - {% endif %}Login OTP',
    'Hello {{ user_name }},
OTP: {{ otp }}
Valid: {{ valid_minutes }} min
{% if school_name %}{{ school_name }}{% else %}ShikshaWave{% endif %}',
    '<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body style="margin:0;padding:20px;font-family:Arial,sans-serif;background:#fff"><div style="max-width:500px;margin:0 auto;padding:30px;border:2px solid #e0e0e0;border-radius:8px"><h2 style="margin:0 0 20px;color:#333;font-size:24px">{% if school_name %}{{ school_name }}{% else %}ShikshaWave{% endif %}</h2><p style="margin:0 0 15px;color:#666;font-size:15px">Hello {{ user_name }},</p><div style="background:#f5f5f5;padding:20px;border-radius:6px;text-align:center;margin:20px 0"><span style="font-size:36px;font-weight:bold;color:#333;letter-spacing:6px;font-family:monospace">{{ otp }}</span></div><p style="margin:15px 0;color:#666;font-size:14px">Valid for {{ valid_minutes }} minutes</p><p style="margin:15px 0;color:#999;font-size:12px">IP: {{ ip_address }}</p></div></body></html>',
    'ShikshaWave <shikshawaves@gmail.com>',
    NULL,
    NULL,
    '{"user_name":"User name","otp":"6-digit code","valid_minutes":"15","ip_address":"IP","school_name":"School name (optional)"}',
    0,
    GETDATE(),
    GETDATE()
);

-- Template 3: Professional Blue
INSERT INTO EmailTemplate (Code, SchoolId, Language, SubjectTemplate, BodyTextTemplate, BodyHtmlTemplate, DefaultFrom, Cc, Bcc, Placeholders, IsActive, CreatedAt, UpdatedAt)
VALUES (
    'LOGIN_OTP_PROFESSIONAL',
    NULL,
    'en',
    '{% if school_name %}{{ school_name }} - {% endif %}Secure Login Code',
    'Hello {{ user_name }},
OTP: {{ otp }}
Valid: {{ valid_minutes }} min
{% if school_name %}{{ school_name }}{% else %}ShikshaWave{% endif %}',
    '<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body style="margin:0;padding:0;font-family:Arial,sans-serif;background:#f0f4f8"><table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4f8;padding:30px 0"><tr><td align="center"><table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:8px;overflow:hidden"><tr><td style="background:#1e3a8a;padding:30px;text-align:center"><h1 style="margin:0;color:#fff;font-size:26px">{% if school_name %}{{ school_name }}{% else %}ShikshaWave{% endif %}</h1></td></tr><tr><td style="padding:40px 30px"><p style="margin:0 0 20px;color:#333;font-size:16px">Hello <strong>{{ user_name }}</strong>,</p><p style="margin:0 0 20px;color:#666;font-size:14px">Your secure login code:</p><div style="background:#eff6ff;border:2px solid #1e3a8a;border-radius:8px;padding:20px;text-align:center;margin:20px 0"><span style="font-size:40px;font-weight:bold;color:#1e3a8a;letter-spacing:10px;font-family:monospace">{{ otp }}</span></div><p style="margin:20px 0;color:#666;font-size:13px">⏱️ Expires in {{ valid_minutes }} minutes | 📍 IP: {{ ip_address }}</p></td></tr><tr><td style="background:#f8fafc;padding:20px;text-align:center;border-top:1px solid #e5e7eb"><p style="margin:0;color:#64748b;font-size:11px">© 2024 {% if school_name %}{{ school_name }}{% else %}ShikshaWave{% endif %}</p></td></tr></table></td></tr></table></body></html>',
    'ShikshaWave <shikshawaves@gmail.com>',
    NULL,
    NULL,
    '{"user_name":"User name","otp":"6-digit code","valid_minutes":"15","ip_address":"IP","school_name":"School name (optional)"}',
    0,
    GETDATE(),
    GETDATE()
);

PRINT 'Created 3 OTP email templates:';
PRINT '1. LOGIN_OTP (Active) - Modern Gradient';
PRINT '2. LOGIN_OTP_MINIMAL - Minimal Clean';
PRINT '3. LOGIN_OTP_PROFESSIONAL - Professional Blue';
GO
