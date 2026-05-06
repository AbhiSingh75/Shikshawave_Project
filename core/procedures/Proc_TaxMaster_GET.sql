-- Function: Proc_TaxMaster_GET
-- Purpose: Retrieve Tax Configurations (Single or List)

CREATE OR REPLACE FUNCTION public."Proc_TaxMaster_GET"(
    p_TaxID INT DEFAULT NULL,
    p_IsActive BOOLEAN DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_agg(t) INTO result
    FROM (
        SELECT 
            "TaxID",
            "TaxName",
            "TaxPercentage",
            "TaxCode",
            "IsInclusive",
            "IsActive",
            "CreatedBy",
            "CreatedAt",
            "UpdatedAt"
        FROM "TaxMaster"
        WHERE (p_TaxID IS NULL OR "TaxID" = p_TaxID)
          AND (p_IsActive IS NULL OR "IsActive" = p_IsActive)
        ORDER BY "TaxID" DESC
    ) t;

    RETURN COALESCE(result, '[]'::jsonb);
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'Error', SQLERRM,
        'Status', 'Error'
    );
END;
$$ LANGUAGE plpgsql;
