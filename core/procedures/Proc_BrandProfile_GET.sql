-- Description: Fetches the first active Brand Profile for invoicing and branding.
-- Returns: JSONB object containing BrandName, BrandLogo (base64 serialized), GSTIN, etc.

CREATE OR REPLACE FUNCTION "Proc_BrandProfile_GET"()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'BrandName', "BrandName",
        'BrandLogo', encode("BrandLogo", 'base64'),
        'GSTIN', "GSTIN",
        'Address', "Address",
        'Phone', "Phone",
        'Email', "Email",
        'Website', "Website",
        'AuthorizedSignatory', "AuthorizedSignatory",
        'AuthorizedSignature', encode("AuthorizedSignature", 'base64')
    ) INTO result
    FROM "BrandProfile"
    WHERE "IsActive" = TRUE
    ORDER BY "ProfileID" ASC
    LIMIT 1;

    RETURN COALESCE(result, '{}'::JSONB);
END;
$$ LANGUAGE plpgsql;
