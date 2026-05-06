# Generated migration for upgraded fee report procedure

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0038_create_fee_report_procedure'),
    ]

    operations = [
        migrations.RunSQL(
            """
            IF EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = 'USP_GetFeeReport')
                DROP PROCEDURE USP_GetFeeReport;
            """
        ),
        migrations.RunSQL(
            """
            CREATE PROCEDURE USP_GetFeeReport
            (
                @mint_SchoolID INT,
                @mvar_FromDate DATE = NULL,
                @mvar_ToDate DATE = NULL,
                @mvar_ClassID INT = NULL,
                @mvar_SectionID INT = NULL,
                @mvar_FeeMonth NVARCHAR(6) = NULL,
                @mvar_StudentName NVARCHAR(255) = NULL,
                @mvar_StudentCode NVARCHAR(50) = NULL,
                @mvar_Email NVARCHAR(255) = NULL,
                @mvar_PaymentStatus NVARCHAR(20) = NULL,
                @mvar_ShowReportList BIT = 0
            )
            AS
            BEGIN
                SET NOCOUNT ON;
                
                -- Set defaults
                IF @mvar_FromDate IS NULL SET @mvar_FromDate = DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1);
                IF @mvar_ToDate IS NULL SET @mvar_ToDate = EOMONTH(GETDATE());
                
                -- Calculate overview/card data
                DECLARE @TotalGenerated DECIMAL(18,2) = 0;
                DECLARE @TotalCollected DECIMAL(18,2) = 0;
                DECLARE @TotalPending DECIMAL(18,2) = 0;
                DECLARE @TotalStudentsBilled INT = 0;
                DECLARE @CollectionPercentage DECIMAL(5,2) = 0;
                DECLARE @PaidAmountTotal DECIMAL(18,2) = 0;
                DECLARE @PartialAmountTotal DECIMAL(18,2) = 0;
                DECLARE @PendingAmountTotal DECIMAL(18,2) = 0;
                
                -- Get totals from Student_Fee_Assignment
                SELECT 
                    @TotalGenerated = ISNULL(SUM(sfa.FinalAmount), 0),
                    @TotalStudentsBilled = COUNT(DISTINCT sfa.StudentID)
                FROM Student_Fee_Assignment sfa
                INNER JOIN Student s ON sfa.StudentID = s.StudentID
                WHERE sfa.SchoolID = @mint_SchoolID
                    AND sfa.IsDeleted = 0
                    AND (@mvar_ClassID IS NULL OR s.AdmissionClass = @mvar_ClassID)
                    AND (@mvar_SectionID IS NULL OR s.Section = @mvar_SectionID)
                    AND (@mvar_FeeMonth IS NULL OR sfa.FeeMonth = @mvar_FeeMonth)
                    AND (@mvar_StudentCode IS NULL OR s.StudentCode = @mvar_StudentCode)
                    AND (@mvar_StudentName IS NULL OR s.FullName LIKE '%' + @mvar_StudentName + '%')
                    AND (@mvar_Email IS NULL OR s.Email = @mvar_Email);
                
                -- Get collected amount from Payment table
                SELECT 
                    @TotalCollected = ISNULL(SUM(p.PaidAmount), 0)
                FROM Payment p
                INNER JOIN Student s ON p.EntityID = s.StudentID
                WHERE p.SchoolID = @mint_SchoolID
                    AND p.EntityType = 'Student'
                    AND p.PaymentFor = 'Fees'
                    AND p.IsDeleted = 0
                    AND p.PaymentDate BETWEEN @mvar_FromDate AND @mvar_ToDate
                    AND (@mvar_ClassID IS NULL OR s.AdmissionClass = @mvar_ClassID)
                    AND (@mvar_SectionID IS NULL OR s.Section = @mvar_SectionID)
                    AND (@mvar_StudentCode IS NULL OR s.StudentCode = @mvar_StudentCode)
                    AND (@mvar_StudentName IS NULL OR s.FullName LIKE '%' + @mvar_StudentName + '%')
                    AND (@mvar_Email IS NULL OR s.Email = @mvar_Email);
                
                -- Calculate pending and percentages
                SET @TotalPending = @TotalGenerated - @TotalCollected;
                IF @TotalGenerated > 0 
                    SET @CollectionPercentage = (@TotalCollected / @TotalGenerated) * 100;
                
                -- Get payment status breakdown
                SELECT 
                    @PaidAmountTotal = ISNULL(SUM(CASE WHEN p.PaidAmount = p.TotalAmount THEN p.PaidAmount ELSE 0 END), 0),
                    @PartialAmountTotal = ISNULL(SUM(CASE WHEN p.PaidAmount > 0 AND p.PaidAmount < p.TotalAmount THEN p.PaidAmount ELSE 0 END), 0),
                    @PendingAmountTotal = ISNULL(SUM(CASE WHEN p.PaidAmount = 0 THEN p.TotalAmount ELSE 0 END), 0)
                FROM Payment p
                INNER JOIN Student s ON p.EntityID = s.StudentID
                WHERE p.SchoolID = @mint_SchoolID
                    AND p.EntityType = 'Student'
                    AND p.PaymentFor = 'Fees'
                    AND p.IsDeleted = 0
                    AND p.PaymentDate BETWEEN @mvar_FromDate AND @mvar_ToDate
                    AND (@mvar_ClassID IS NULL OR s.AdmissionClass = @mvar_ClassID)
                    AND (@mvar_SectionID IS NULL OR s.Section = @mvar_SectionID)
                    AND (@mvar_StudentCode IS NULL OR s.StudentCode = @mvar_StudentCode)
                    AND (@mvar_StudentName IS NULL OR s.FullName LIKE '%' + @mvar_StudentName + '%')
                    AND (@mvar_Email IS NULL OR s.Email = @mvar_Email);
                
                -- Return overview/card data (First result set)
                SELECT 
                    @TotalGenerated AS TotalGenerated,
                    @TotalCollected AS TotalCollected,
                    @TotalPending AS TotalPending,
                    @TotalStudentsBilled AS TotalStudentsBilled,
                    @CollectionPercentage AS CollectionPercentage,
                    @PaidAmountTotal AS PaidAmountTotal,
                    @PartialAmountTotal AS PartialAmountTotal,
                    @PendingAmountTotal AS PendingAmountTotal;
                
                -- Return detailed report list if requested (Second result set)
                IF @mvar_ShowReportList = 1
                BEGIN
                    SELECT 
                        s.StudentCode,
                        s.FullName AS StudentName,
                        c.ClassName,
                        ISNULL(sec.SectionName, 'N/A') AS SectionName,
                        s.Email,
                        s.ParentMobile,
                        ISNULL(SUM(sfa.FinalAmount), 0) AS TotalFeeAmount,
                        ISNULL(SUM(p.PaidAmount), 0) AS PaidAmount,
                        ISNULL(SUM(sfa.FinalAmount), 0) - ISNULL(SUM(p.PaidAmount), 0) AS PendingAmount,
                        CASE 
                            WHEN ISNULL(SUM(p.PaidAmount), 0) = 0 THEN 'Unpaid'
                            WHEN ISNULL(SUM(p.PaidAmount), 0) >= ISNULL(SUM(sfa.FinalAmount), 0) THEN 'Paid'
                            ELSE 'Partial'
                        END AS PaymentStatus,
                        MAX(p.PaymentDate) AS LastPaymentDate,
                        MAX(p.ReceiptNumber) AS LastReceiptNumber
                    FROM Student s
                    INNER JOIN ClassMaster c ON s.AdmissionClass = c.ClassID
                    LEFT JOIN SectionMaster sec ON s.Section = sec.SectionID
                    LEFT JOIN Student_Fee_Assignment sfa ON s.StudentID = sfa.StudentID 
                        AND sfa.SchoolID = @mint_SchoolID 
                        AND sfa.IsDeleted = 0
                        AND (@mvar_FeeMonth IS NULL OR sfa.FeeMonth = @mvar_FeeMonth)
                    LEFT JOIN Payment p ON s.StudentID = p.EntityID 
                        AND p.EntityType = 'Student' 
                        AND p.PaymentFor = 'Fees'
                        AND p.SchoolID = @mint_SchoolID
                        AND p.IsDeleted = 0
                        AND p.PaymentDate BETWEEN @mvar_FromDate AND @mvar_ToDate
                    WHERE s.SchoolID = @mint_SchoolID
                        AND s.IsDeleted = 0
                        AND (@mvar_ClassID IS NULL OR s.AdmissionClass = @mvar_ClassID)
                        AND (@mvar_SectionID IS NULL OR s.Section = @mvar_SectionID)
                        AND (@mvar_StudentCode IS NULL OR s.StudentCode = @mvar_StudentCode)
                        AND (@mvar_StudentName IS NULL OR s.FullName LIKE '%' + @mvar_StudentName + '%')
                        AND (@mvar_Email IS NULL OR s.Email = @mvar_Email)
                    GROUP BY s.StudentID, s.StudentCode, s.FullName, c.ClassName, sec.SectionName, s.Email, s.ParentMobile
                    HAVING (@mvar_PaymentStatus IS NULL 
                        OR (@mvar_PaymentStatus = 'Paid' AND ISNULL(SUM(p.PaidAmount), 0) >= ISNULL(SUM(sfa.FinalAmount), 0))
                        OR (@mvar_PaymentStatus = 'Unpaid' AND ISNULL(SUM(p.PaidAmount), 0) = 0)
                        OR (@mvar_PaymentStatus = 'Partial' AND ISNULL(SUM(p.PaidAmount), 0) > 0 AND ISNULL(SUM(p.PaidAmount), 0) < ISNULL(SUM(sfa.FinalAmount), 0)))
                    ORDER BY s.StudentCode;
                END
            END
            """,
            reverse_sql="IF EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = 'USP_GetFeeReport') DROP PROCEDURE USP_GetFeeReport"
        ),
    ]
