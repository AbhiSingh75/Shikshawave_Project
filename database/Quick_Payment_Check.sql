-- Quick diagnostic to check payment data availability

-- 1. Check if Payment table has any data
SELECT 'Total Payments' AS CheckType, COUNT(*) AS Count
FROM Payment
WHERE IsDeleted = 0;

-- 2. Check payments in current month
SELECT 'Current Month Payments' AS CheckType, COUNT(*) AS Count
FROM Payment
WHERE IsDeleted = 0
  AND MONTH(PaymentDate) = MONTH(GETDATE())
  AND YEAR(PaymentDate) = YEAR(GETDATE());

-- 3. Check payments in last 6 months
SELECT 'Last 6 Months Payments' AS CheckType, COUNT(*) AS Count
FROM Payment
WHERE IsDeleted = 0
  AND PaymentDate >= DATEADD(MONTH, -6, GETDATE());

-- 4. Check sample payment records
SELECT TOP 5 
    PaymentID,
    PaymentFor,
    EntityID,
    PaidAmount,
    PaymentDate,
    PaymentMode
FROM Payment
WHERE IsDeleted = 0
ORDER BY PaymentDate DESC;

-- 5. Check if EntityID links to Student table
SELECT 'Payments with Valid Student Link' AS CheckType, COUNT(*) AS Count
FROM Payment p
INNER JOIN Student s ON p.EntityID = s.StudentID
WHERE p.IsDeleted = 0 AND s.IsDeleted = 0;
