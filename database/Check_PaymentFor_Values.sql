-- Check what PaymentFor values exist in Payment table
SELECT DISTINCT PaymentFor, COUNT(*) AS Count
FROM Payment
WHERE IsDeleted = 0 AND SchoolID = 3
GROUP BY PaymentFor;

-- Check specific payments
SELECT TOP 10
    PaymentID,
    PaymentFor,
    PaidAmount,
    PaymentDate,
    LEN(PaymentFor) AS Length,
    ASCII(LEFT(PaymentFor, 1)) AS FirstChar,
    ASCII(RIGHT(PaymentFor, 1)) AS LastChar
FROM Payment
WHERE IsDeleted = 0 AND SchoolID = 3
ORDER BY PaymentDate DESC;
