-- Create mail_emailtemplate table
CREATE TABLE mail_emailtemplate (
    id INT IDENTITY(1,1) PRIMARY KEY,
    template_name NVARCHAR(100) NOT NULL,
    subject NVARCHAR(255) NOT NULL,
    body NVARCHAR(MAX) NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    is_active BIT DEFAULT 1
);

-- Add some default templates (optional)
INSERT INTO mail_emailtemplate (template_name, subject, body) VALUES
('welcome', 'Welcome to ShikshaWave', 'Welcome {{name}}! Your account has been created.'),
('employee_added', 'New Employee Added', 'Employee {{name}} has been added to the system.');
