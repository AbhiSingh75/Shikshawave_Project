-- Add default SALARY_SLIP email template
-- Run this script if the template doesn't exist in your database

-- Check if template already exists
IF NOT EXISTS (SELECT 1 FROM EmailTemplate WHERE Code = 'SALARY_SLIP' AND SchoolId IS NULL AND Language = 'en')
BEGIN
    INSERT INTO EmailTemplate (
        Code, 
        SchoolId, 
        Language, 
        SubjectTemplate, 
        BodyTextTemplate, 
        BodyHtmlTemplate, 
        IsActive, 
        CreatedAt, 
        UpdatedAt
    )
    VALUES (
        'SALARY_SLIP',
        NULL,
        'en',
        'Salary Slip for {{ month }} {{ year }}',
        'Dear {{ employee_name }},

Please find attached your salary slip for {{ month }} {{ year }}.

Gross Salary: {{ gross_salary }}
Net Salary: {{ net_salary }}

Best regards,
{{ school_name }}',
        '<html>
<body>
    <p>Dear <strong>{{ employee_name }}</strong>,</p>
    <p>Please find attached your salary slip for <strong>{{ month }} {{ year }}</strong>.</p>
    <table border="1" cellpadding="5" style="border-collapse: collapse;">
        <tr>
            <td><strong>Gross Salary:</strong></td>
            <td>{{ gross_salary }}</td>
        </tr>
        <tr>
            <td><strong>Net Salary:</strong></td>
            <td>{{ net_salary }}</td>
        </tr>
    </table>
    <p>Best regards,<br><strong>{{ school_name }}</strong></p>
</body>
</html>',
        1,
        GETDATE(),
        GETDATE()
    );
    
    PRINT 'Default SALARY_SLIP template added successfully';
END
ELSE
BEGIN
    PRINT 'Default SALARY_SLIP template already exists';
END
