-- Check for SchoolID mismatch between Payment and Student tables

-- 1. Check SchoolIDs in Payment table
SELECT DISTINCT 'Payment SchoolID' AS Source, SchoolID, COUNT(*) AS Count
FROM Payment
WHERE IsDeleted = 0
GROUP BY SchoolID;

-- 2. Check SchoolIDs in Student table
SELECT DISTINCT 'Student SchoolID' AS Source, SchoolID, COUNT(*) AS Count
FROM Student
WHERE IsDeleted = 0
GROUP BY SchoolID;

-- 3. Check if Payment.EntityID students have matching SchoolID
SELECT 
    p.SchoolID AS Payment_SchoolID,
    s.SchoolID AS Student_SchoolID,
    COUNT(*) AS MismatchCount
FROM Payment p
INNER JOIN Student s ON p.EntityID = s.StudentID
WHERE p.IsDeleted = 0 AND s.IsDeleted = 0
  AND p.SchoolID != s.SchoolID
GROUP BY p.SchoolID, s.SchoolID;

-- 4. Show sample payment with student details
SELECT TOP 5
    p.PaymentID,
    p.SchoolID AS Payment_SchoolID,
    p.EntityID AS StudentID,
    s.SchoolID AS Student_SchoolID,
    s.StudentName,
    p.PaidAmount,
    p.PaymentDate
FROM Payment p
INNER JOIN Student s ON p.EntityID = s.StudentID
WHERE p.IsDeleted = 0 AND s.IsDeleted = 0
ORDER BY p.PaymentDate DESC;
