-- Function: Proc_TaxMaster_SET
-- Purpose: Save, Update or Delete Tax Configurations

CREATE OR REPLACE FUNCTION public."Proc_TaxMaster_SET"(
    p_Action VARCHAR(20),
    p_TaxID INT DEFAULT NULL,
    p_TaxName VARCHAR(100) DEFAULT NULL,
    p_TaxPercentage NUMERIC(5,2) DEFAULT NULL,
    p_TaxCode VARCHAR(50) DEFAULT NULL,
    p_IsInclusive BOOLEAN DEFAULT TRUE,
    p_IsActive BOOLEAN DEFAULT TRUE,
    p_UserID INT DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_TaxID INT;
    v_Message VARCHAR(255);
    v_Status VARCHAR(20);
BEGIN
    IF p_Action = 'SAVE' OR p_Action = 'INSERT' THEN
        INSERT INTO "TaxMaster" (
            "TaxName", "TaxPercentage", "TaxCode", "IsInclusive", "IsActive", "CreatedBy"
        )
        VALUES (
            p_TaxName, p_TaxPercentage, p_TaxCode, p_IsInclusive, p_IsActive, p_UserID
        )
        RETURNING "TaxID" INTO v_TaxID;
        v_Message := 'Tax configuration saved successfully.';
        v_Status := 'Success';
        
    ELSIF p_Action = 'UPDATE' THEN
        UPDATE "TaxMaster"
        SET "TaxName" = COALESCE(p_TaxName, "TaxName"),
            "TaxPercentage" = COALESCE(p_TaxPercentage, "TaxPercentage"),
            "TaxCode" = COALESCE(p_TaxCode, "TaxCode"),
            "IsInclusive" = COALESCE(p_IsInclusive, "IsInclusive"),
            "IsActive" = COALESCE(p_IsActive, "IsActive"),
            "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE "TaxID" = p_TaxID;
        
        v_TaxID := p_TaxID;
        v_Message := 'Tax configuration updated successfully.';
        v_Status := 'Success';
        
    ELSIF p_Action = 'DELETE' THEN
        DELETE FROM "TaxMaster" WHERE "TaxID" = p_TaxID;
        v_Message := 'Tax configuration deleted successfully.';
        v_Status := 'Success';
    ELSE
        v_Status := 'Error';
        v_Message := 'Invalid Action Specified.';
    END IF;

    RETURN jsonb_build_object(
        'TaxID', v_TaxID,
        'Message', v_Message,
        'Status', v_Status
    );
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'TaxID', p_TaxID,
        'Message', SQLERRM,
        'Status', 'Error'
    );
END;
$$ LANGUAGE plpgsql;
