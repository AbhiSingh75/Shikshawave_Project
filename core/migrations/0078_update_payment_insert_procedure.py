from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0077_apply_final_fee_procedure'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
CREATE OR REPLACE FUNCTION public."Proc_Payment_Insert"(
	"p_SchoolID" integer,
	"p_PaymentFor" character varying,
	"p_EntityID" integer,
	"p_EntityType" character varying,
	"p_ReceiptNumber" character varying,
	"p_TotalAmount" numeric,
	"p_PaidAmount" numeric,
	"p_PaymentMode" character varying,
	"p_TransactionRef" character varying DEFAULT NULL::character varying,
	"p_PaymentStatus" character varying DEFAULT NULL::character varying,
	"p_PaymentDate" timestamp without time zone DEFAULT NULL::timestamp without time zone,
	"p_PaymentMonth" character varying DEFAULT NULL::character varying,
	"p_FeeBreakdown" text DEFAULT NULL::text,
	"p_Remarks" character varying DEFAULT NULL::character varying,
	"p_CreatedBy" integer DEFAULT NULL::integer,
	"p_IsDeleted" boolean DEFAULT false,
	"p_discountValue" numeric DEFAULT NULL::numeric)
    RETURNS text
    LANGUAGE 'plpgsql'
AS $BODY$
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
        "Discountvalue"
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
        WHEN COALESCE("Discountvalue", 0) + "PaidAmount" >= "TotalAmount" THEN 'Paid' 
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
$BODY$;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS public.\"Proc_Payment_Insert\"(integer, character varying, integer, character varying, character varying, numeric, numeric, character varying, character varying, character varying, timestamp without time zone, character varying, text, character varying, integer, boolean, numeric);"
        )
    ]
