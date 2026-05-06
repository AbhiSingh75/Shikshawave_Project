from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0071_final_data_retrieval_fix'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
CREATE OR REPLACE FUNCTION public."Proc_Payment_Insert"(
    "p_SchoolID" INT,
    "p_PaymentFor" VARCHAR(50),
    "p_EntityID" INT,
    "p_EntityType" VARCHAR(50),
    "p_ReceiptNumber" VARCHAR(100),
    "p_TotalAmount" NUMERIC(18,2),
    "p_PaidAmount" NUMERIC(18,2),
    "p_PaymentMode" VARCHAR(50),
    "p_TransactionRef" VARCHAR(100) DEFAULT NULL,
    "p_PaymentStatus" VARCHAR(50) DEFAULT NULL,
    "p_PaymentDate" TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL,
    "p_PaymentMonth" VARCHAR(6) DEFAULT NULL,
    "p_FeeBreakdown" TEXT DEFAULT NULL,
    "p_Remarks" VARCHAR(255) DEFAULT NULL,
    "p_CreatedBy" INT DEFAULT NULL,
    "p_IsDeleted" BOOLEAN DEFAULT FALSE,
    "p_discountValue" NUMERIC(16,2) DEFAULT NULL
)
RETURNS text
LANGUAGE plpgsql
AS $$
DECLARE
    v_MonthYearStr VARCHAR(20);
    v_NewPaymentID INT;
    v_TempDate DATE;
BEGIN
    -- Convert YYYYMM to short month + year (e.g., Sep 2025)
    BEGIN
        v_TempDate := to_date("p_PaymentMonth" || '01', 'YYYYMMDD');
        v_MonthYearStr := to_char(v_TempDate, 'Mon YYYY');
    EXCEPTION WHEN OTHERS THEN
        v_MonthYearStr := "p_PaymentMonth";
    END;

    -- check duplicate payment for same month
    IF EXISTS (
        SELECT 1
        FROM "Payment"
        WHERE "SchoolID" = "p_SchoolID"
          AND "EntityID" = "p_EntityID"
          AND "EntityType" = "p_EntityType"
          AND "PaymentFor" = "p_PaymentFor"
          AND "PaymentMonth" = "p_PaymentMonth"
          AND "IsDeleted" = FALSE
    ) THEN
        RETURN json_build_object(
            'status', 'Error',
            'message', 'Payment already exists for ' || v_MonthYearStr
        )::text;
    END IF;

    -- Extract discountValue from FeeBreakdown JSON
    IF "p_FeeBreakdown" IS NOT NULL AND "p_FeeBreakdown" != '' THEN
        BEGIN
            SELECT CAST(elem->>'userEnterAmount' AS NUMERIC(16,2)) INTO "p_discountValue"
            FROM json_array_elements("p_FeeBreakdown"::json) AS elem
            WHERE elem->>'feeTypeName' ILIKE '%Monthly Fee Discount%';
        EXCEPTION WHEN OTHERS THEN
            "p_discountValue" := 0;
        END;
    END IF;

    "p_discountValue" := COALESCE("p_discountValue", 0);

    -- insert new payment
    INSERT INTO "Payment"
    (
        "SchoolID",
        "PaymentFor",
        "EntityID",
        "EntityType",
        "ReceiptNumber",
        "TotalAmount",
        "PaidAmount",
        "PaymentMode",
        "TransactionRef",
        "PaymentStatus",
        "PaymentDate",
        "PaymentMonth",
        "FeeBreakdown",
        "Remarks",
        "CreatedBy",
        "CreatedAt",
        "IsDeleted",
        "discountValue"
    )
    VALUES
    (
        "p_SchoolID",
        "p_PaymentFor",
        "p_EntityID",
        "p_EntityType",
        "p_ReceiptNumber",
        "p_TotalAmount",
        "p_PaidAmount",
        "p_PaymentMode",
        "p_TransactionRef",
        "p_PaymentStatus",
        "p_PaymentDate",
        "p_PaymentMonth",
        "p_FeeBreakdown",
        "p_Remarks",
        "p_CreatedBy",
        CURRENT_TIMESTAMP,
        "p_IsDeleted",
        "p_discountValue"
    )
    RETURNING "PaymentID" INTO v_NewPaymentID;

    UPDATE "Payment" 
    SET "PaymentStatus" = CASE 
        WHEN COALESCE("discountValue", 0) + "PaidAmount" >= "TotalAmount" THEN 'Paid' 
        ELSE "PaymentStatus" 
    END 
    WHERE "PaymentID" = v_NewPaymentID;

    RETURN json_build_object(
        'status', 'Success',
        'message', 'Payment inserted successfully',
        'PaymentID', v_NewPaymentID
    )::text;

EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'status', 'Error',
        'message', SQLERRM
    )::text;
END;
$$;
            ''',
            reverse_sql='DROP FUNCTION IF EXISTS public."Proc_Payment_Insert";'
        )
    ]
