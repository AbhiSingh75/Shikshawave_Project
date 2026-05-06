-- PostgreSQL functions for School - using actual SchoolMaster columns
-- SchoolMaster has BoardID, MediumID, Principal/Director fields directly

-- 1. Get school details by ID
CREATE OR REPLACE FUNCTION "Proc_GetSchoolDetails_ByID"(p_SchoolID INT)
RETURNS TABLE (
    "SchoolID" INT,
    "SchoolCode" VARCHAR,
    "SchoolName" VARCHAR,
    "RegistrationNumber" VARCHAR,
    "Address" TEXT,
    "District" VARCHAR,
    "State" VARCHAR,
    "Country" VARCHAR,
    "Pincode" VARCHAR,
    "Phone" VARCHAR,
    "Email" VARCHAR,
    "Website" VARCHAR,
    "SchoolLogo" BYTEA,
    "BoardID" INT,
    "BoardName" VARCHAR,
    "MediumID" INT,
    "MediumName" VARCHAR,
    "PrincipalName" VARCHAR,
    "PrincipalContactMail" VARCHAR,
    "PrincipalContactPhone" VARCHAR,
    "DirectorName" VARCHAR,
    "DirectorContactPhone" VARCHAR,
    "DirectorContactEmail" VARCHAR,
    "EstablishDate" DATE,
    "CreatedAt" TIMESTAMP,
    "Status" VARCHAR,
    "ErrorMessage" VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sm."SchoolID",
        sm."SchoolCode",
        sm."SchoolName",
        sm."RegistrationNumber",
        sm."Address"::TEXT,
        sm."District"::VARCHAR,
        sm."State"::VARCHAR,
        sm."Country"::VARCHAR,
        sm."Pincode",
        sm."Phone",
        sm."Email",
        sm."Website",
        sm."SchoolLogo",
        sm."BoardID",
        COALESCE(bm."BoardName", 'N/A')::VARCHAR,
        sm."MediumID",
        COALESCE(mm."MediumName", 'N/A')::VARCHAR,
        sm."PrincipalName",
        sm."PrincipalContactMail",
        sm."PrincipalContactPhone",
        sm."DirectorName",
        sm."DirectorContactPhone",
        sm."DirectorContactEmail",
        sm."EstablishDate",
        sm."CreatedAt",
        'Success'::VARCHAR,
        ''::VARCHAR
    FROM "SchoolMaster" sm
    LEFT JOIN "Board_Master" bm ON sm."BoardID" = bm."BoardID" AND bm."IsDeleted" = FALSE
    LEFT JOIN "Medium_Master" mm ON sm."MediumID" = mm."MediumID" AND mm."IsDeleted" = FALSE
    WHERE sm."SchoolID" = p_SchoolID;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT 
            NULL::INT, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::TEXT,
            NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR,
            NULL::VARCHAR, NULL::VARCHAR, NULL::BYTEA, NULL::INT, NULL::VARCHAR,
            NULL::INT, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR,
            NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::DATE, NULL::TIMESTAMP,
            'Error'::VARCHAR, 'School not found'::VARCHAR;
    END IF;
END;
$$ LANGUAGE plpgsql;


-- 2. Update school
CREATE OR REPLACE FUNCTION "Proc_UpdateSchool_Set"(
    p_SchoolID INT,
    p_SchoolName VARCHAR,
    p_RegistrationNumber VARCHAR,
    p_Address TEXT,
    p_District INT,
    p_State INT,
    p_Country INT,
    p_Pincode VARCHAR,
    p_Phone VARCHAR,
    p_Email VARCHAR,
    p_Website VARCHAR,
    p_UpdatedBy INT,
    p_SchoolLogo BYTEA,
    p_BoardID INT,
    p_MediumID INT,
    p_PrincipalName VARCHAR,
    p_PrincipalContactMail VARCHAR,
    p_PrincipalContactPhone VARCHAR,
    p_DirectorName VARCHAR,
    p_DirectorContactPhone VARCHAR,
    p_DirectorContactEmail VARCHAR,
    p_EstablishDate DATE
) RETURNS TABLE (
    "Status" VARCHAR,
    "ErrorMessage" VARCHAR
) AS $$
BEGIN
    UPDATE "SchoolMaster" SET
        "SchoolName" = p_SchoolName,
        "RegistrationNumber" = p_RegistrationNumber,
        "Address" = p_Address,
        "District" = p_District,
        "State" = p_State,
        "Country" = p_Country,
        "Pincode" = p_Pincode,
        "Phone" = p_Phone,
        "Email" = p_Email,
        "Website" = p_Website,
        "SchoolLogo" = COALESCE(p_SchoolLogo, "SchoolLogo"),
        "BoardID" = p_BoardID,
        "MediumID" = p_MediumID,
        "PrincipalName" = p_PrincipalName,
        "PrincipalContactMail" = p_PrincipalContactMail,
        "PrincipalContactPhone" = p_PrincipalContactPhone,
        "DirectorName" = p_DirectorName,
        "DirectorContactPhone" = p_DirectorContactPhone,
        "DirectorContactEmail" = p_DirectorContactEmail,
        "EstablishDate" = p_EstablishDate,
        "UpdatedBy" = p_UpdatedBy,
        "UpdatedAt" = CURRENT_TIMESTAMP
    WHERE "SchoolID" = p_SchoolID;
    
    RETURN QUERY SELECT 'Success'::VARCHAR, ''::VARCHAR;
    
EXCEPTION
    WHEN OTHERS THEN
        RETURN QUERY SELECT 'Error'::VARCHAR, SQLERRM::VARCHAR;
END;
$$ LANGUAGE plpgsql;


-- 3. List schools with filters
CREATE OR REPLACE FUNCTION "Proc_SchoolList_get"(
    p_SearchCreatedAt DATE, p_SearchToDate DATE, p_SearchSchoolCode VARCHAR,
    p_SearchSchoolName VARCHAR, p_SearchCountry INT, p_SearchState INT,
    p_SearchDistrict INT, p_SearchPhone VARCHAR, p_SearchEmail VARCHAR,
    p_SearchBoard INT, p_SearchMedium INT, p_SearchPincode VARCHAR,
    p_SearchRegistrationNumber VARCHAR, p_SearchPrincipalName VARCHAR,
    p_SearchDirectorName VARCHAR, p_SearchStatus VARCHAR, p_ShowDeleted BOOLEAN,
    p_SortColumn VARCHAR, p_SortDirection VARCHAR, p_PageNumber INT,
    p_PageSize INT, p_UserId INT,
    p_FilterSchoolID INT DEFAULT NULL  -- Added for role-based filtering
) RETURNS TABLE (
    "SchoolID" INT, "SchoolCode" VARCHAR, "SchoolName" VARCHAR,
    "RegistrationNumber" VARCHAR, "Address" TEXT, "DistrictName" VARCHAR,
    "StateName" VARCHAR, "CountryName" VARCHAR, "Pincode" VARCHAR,
    "Phone" VARCHAR, "Email" VARCHAR, "Website" VARCHAR,
    "SchoolLogo" BYTEA, "BoardName" VARCHAR, "MediumName" VARCHAR,
    "PrincipalName" VARCHAR, "PrincipalContactMail" VARCHAR,
    "PrincipalContactPhone" VARCHAR, "DirectorName" VARCHAR,
    "DirectorContactPhone" VARCHAR, "DirectorContactEmail" VARCHAR,
    "EstablishDate" DATE, "CreatedAt" TIMESTAMP, "STATUS" VARCHAR,
    "IsDeleted" BOOLEAN,
    "TotalCount" BIGINT, "ActiveSchools" BIGINT, "DeletedSchools" BIGINT
) AS $$
DECLARE
    v_Offset INT := (p_PageNumber - 1) * p_PageSize;
    v_TotalCount BIGINT;
    v_ActiveCount BIGINT;
    v_DeletedCount BIGINT;
BEGIN
    -- Update counts based on FilterSchoolID and Search Filters
    SELECT COUNT(*) INTO v_TotalCount FROM "SchoolMaster" sm 
    WHERE (p_ShowDeleted OR NOT sm."IsDeleted")
    AND (p_FilterSchoolID IS NULL OR sm."SchoolID" = p_FilterSchoolID)
    AND (p_SearchSchoolCode IS NULL OR sm."SchoolCode" ILIKE '%' || p_SearchSchoolCode || '%')
    AND (p_SearchSchoolName IS NULL OR sm."SchoolName" ILIKE '%' || p_SearchSchoolName || '%')
    AND (p_SearchCountry IS NULL OR sm."Country" = p_SearchCountry)
    AND (p_SearchState IS NULL OR sm."State" = p_SearchState)
    AND (p_SearchDistrict IS NULL OR sm."District" = p_SearchDistrict)
    AND (p_SearchPhone IS NULL OR sm."Phone" ILIKE '%' || p_SearchPhone || '%')
    AND (p_SearchEmail IS NULL OR sm."Email" ILIKE '%' || p_SearchEmail || '%')
    AND (p_SearchBoard IS NULL OR sm."BoardID" = p_SearchBoard)
    AND (p_SearchMedium IS NULL OR sm."MediumID" = p_SearchMedium)
    AND (p_SearchPincode IS NULL OR sm."Pincode" ILIKE '%' || p_SearchPincode || '%')
    AND (p_SearchRegistrationNumber IS NULL OR sm."RegistrationNumber" ILIKE '%' || p_SearchRegistrationNumber || '%')
    AND (p_SearchPrincipalName IS NULL OR sm."PrincipalName" ILIKE '%' || p_SearchPrincipalName || '%')
    AND (p_SearchDirectorName IS NULL OR sm."DirectorName" ILIKE '%' || p_SearchDirectorName || '%')
    AND (p_SearchStatus IS NULL OR (CASE WHEN sm."IsDeleted" THEN 'Inactive' ELSE 'Active' END) = p_SearchStatus);

    SELECT COUNT(*) INTO v_ActiveCount FROM "SchoolMaster" sm 
    WHERE NOT sm."IsDeleted"
    AND (p_FilterSchoolID IS NULL OR sm."SchoolID" = p_FilterSchoolID)
    AND (p_SearchSchoolCode IS NULL OR sm."SchoolCode" ILIKE '%' || p_SearchSchoolCode || '%')
    AND (p_SearchSchoolName IS NULL OR sm."SchoolName" ILIKE '%' || p_SearchSchoolName || '%')
    AND (p_SearchCountry IS NULL OR sm."Country" = p_SearchCountry)
    AND (p_SearchState IS NULL OR sm."State" = p_SearchState)
    AND (p_SearchDistrict IS NULL OR sm."District" = p_SearchDistrict)
    AND (p_SearchPhone IS NULL OR sm."Phone" ILIKE '%' || p_SearchPhone || '%')
    AND (p_SearchEmail IS NULL OR sm."Email" ILIKE '%' || p_SearchEmail || '%')
    AND (p_SearchBoard IS NULL OR sm."BoardID" = p_SearchBoard)
    AND (p_SearchMedium IS NULL OR sm."MediumID" = p_SearchMedium)
    AND (p_SearchPincode IS NULL OR sm."Pincode" ILIKE '%' || p_SearchPincode || '%')
    AND (p_SearchRegistrationNumber IS NULL OR sm."RegistrationNumber" ILIKE '%' || p_SearchRegistrationNumber || '%')
    AND (p_SearchPrincipalName IS NULL OR sm."PrincipalName" ILIKE '%' || p_SearchPrincipalName || '%')
    AND (p_SearchDirectorName IS NULL OR sm."DirectorName" ILIKE '%' || p_SearchDirectorName || '%')
    AND (p_SearchStatus IS NULL OR (CASE WHEN sm."IsDeleted" THEN 'Inactive' ELSE 'Active' END) = p_SearchStatus);

    SELECT COUNT(*) INTO v_DeletedCount FROM "SchoolMaster" sm 
    WHERE sm."IsDeleted"
    AND (p_FilterSchoolID IS NULL OR sm."SchoolID" = p_FilterSchoolID)
    AND (p_SearchSchoolCode IS NULL OR sm."SchoolCode" ILIKE '%' || p_SearchSchoolCode || '%')
    AND (p_SearchSchoolName IS NULL OR sm."SchoolName" ILIKE '%' || p_SearchSchoolName || '%')
    AND (p_SearchCountry IS NULL OR sm."Country" = p_SearchCountry)
    AND (p_SearchState IS NULL OR sm."State" = p_SearchState)
    AND (p_SearchDistrict IS NULL OR sm."District" = p_SearchDistrict)
    AND (p_SearchPhone IS NULL OR sm."Phone" ILIKE '%' || p_SearchPhone || '%')
    AND (p_SearchEmail IS NULL OR sm."Email" ILIKE '%' || p_SearchEmail || '%')
    AND (p_SearchBoard IS NULL OR sm."BoardID" = p_SearchBoard)
    AND (p_SearchMedium IS NULL OR sm."MediumID" = p_SearchMedium)
    AND (p_SearchPincode IS NULL OR sm."Pincode" ILIKE '%' || p_SearchPincode || '%')
    AND (p_SearchRegistrationNumber IS NULL OR sm."RegistrationNumber" ILIKE '%' || p_SearchRegistrationNumber || '%')
    AND (p_SearchPrincipalName IS NULL OR sm."PrincipalName" ILIKE '%' || p_SearchPrincipalName || '%')
    AND (p_SearchDirectorName IS NULL OR sm."DirectorName" ILIKE '%' || p_SearchDirectorName || '%')
    AND (p_SearchStatus IS NULL OR (CASE WHEN sm."IsDeleted" THEN 'Inactive' ELSE 'Active' END) = p_SearchStatus);
    
    RETURN QUERY
    SELECT sm."SchoolID", sm."SchoolCode", sm."SchoolName", sm."RegistrationNumber",
           sm."Address"::TEXT, gd."Geog_Name"::VARCHAR, gs."Geog_Name"::VARCHAR,
           gc."Geog_Name"::VARCHAR, sm."Pincode", sm."Phone", sm."Email", sm."Website",
           sm."SchoolLogo", COALESCE(bm."BoardName", 'N/A')::VARCHAR,
           COALESCE(mm."MediumName", 'N/A')::VARCHAR, sm."PrincipalName",
           sm."PrincipalContactMail", sm."PrincipalContactPhone", sm."DirectorName",
           sm."DirectorContactPhone", sm."DirectorContactEmail", sm."EstablishDate",
           sm."CreatedAt", CASE WHEN sm."IsDeleted" THEN 'Inactive' ELSE 'Active' END::VARCHAR,
           sm."IsDeleted",
           v_TotalCount, v_ActiveCount, v_DeletedCount
    FROM "SchoolMaster" sm
    LEFT JOIN "Geographical_Master" gd ON sm."District"::INT = gd."Geog_Id"
    LEFT JOIN "Geographical_Master" gs ON sm."State"::INT = gs."Geog_Id"
    LEFT JOIN "Geographical_Master" gc ON sm."Country"::INT = gc."Geog_Id"
    LEFT JOIN "Board_Master" bm ON sm."BoardID" = bm."BoardID" AND NOT bm."IsDeleted"
    LEFT JOIN "Medium_Master" mm ON sm."MediumID" = mm."MediumID" AND NOT mm."IsDeleted"
    WHERE (p_ShowDeleted OR NOT sm."IsDeleted")
    AND (p_FilterSchoolID IS NULL OR sm."SchoolID" = p_FilterSchoolID)  -- Role-based filter
    AND (p_SearchSchoolCode IS NULL OR sm."SchoolCode" ILIKE '%' || p_SearchSchoolCode || '%')
    AND (p_SearchSchoolName IS NULL OR sm."SchoolName" ILIKE '%' || p_SearchSchoolName || '%')
    AND (p_SearchCountry IS NULL OR sm."Country" = p_SearchCountry)
    AND (p_SearchState IS NULL OR sm."State" = p_SearchState)
    AND (p_SearchDistrict IS NULL OR sm."District" = p_SearchDistrict)
    AND (p_SearchPhone IS NULL OR sm."Phone" ILIKE '%' || p_SearchPhone || '%')
    AND (p_SearchEmail IS NULL OR sm."Email" ILIKE '%' || p_SearchEmail || '%')
    AND (p_SearchBoard IS NULL OR sm."BoardID" = p_SearchBoard)
    AND (p_SearchMedium IS NULL OR sm."MediumID" = p_SearchMedium)
    AND (p_SearchPincode IS NULL OR sm."Pincode" ILIKE '%' || p_SearchPincode || '%')
    AND (p_SearchRegistrationNumber IS NULL OR sm."RegistrationNumber" ILIKE '%' || p_SearchRegistrationNumber || '%')
    AND (p_SearchPrincipalName IS NULL OR sm."PrincipalName" ILIKE '%' || p_SearchPrincipalName || '%')
    AND (p_SearchDirectorName IS NULL OR sm."DirectorName" ILIKE '%' || p_SearchDirectorName || '%')
    AND (p_SearchCreatedAt IS NULL OR sm."CreatedAt"::DATE >= p_SearchCreatedAt)
    AND (p_SearchToDate IS NULL OR sm."CreatedAt"::DATE <= p_SearchToDate)
    AND (p_SearchStatus IS NULL OR (CASE WHEN sm."IsDeleted" THEN 'Inactive' ELSE 'Active' END) = p_SearchStatus)
    ORDER BY 
        CASE WHEN p_SortColumn = 'SchoolID' AND p_SortDirection = 'ASC' THEN sm."SchoolID" END ASC,
        CASE WHEN p_SortColumn = 'SchoolID' AND p_SortDirection = 'DESC' THEN sm."SchoolID" END DESC,
        CASE WHEN p_SortColumn = 'SchoolCode' AND p_SortDirection = 'ASC' THEN sm."SchoolCode" END ASC,
        CASE WHEN p_SortColumn = 'SchoolCode' AND p_SortDirection = 'DESC' THEN sm."SchoolCode" END DESC,
        CASE WHEN p_SortColumn = 'SchoolName' AND p_SortDirection = 'ASC' THEN sm."SchoolName" END ASC,
        CASE WHEN p_SortColumn = 'SchoolName' AND p_SortDirection = 'DESC' THEN sm."SchoolName" END DESC,
        CASE WHEN p_SortColumn = 'RegistrationNumber' AND p_SortDirection = 'ASC' THEN sm."RegistrationNumber" END ASC,
        CASE WHEN p_SortColumn = 'RegistrationNumber' AND p_SortDirection = 'DESC' THEN sm."RegistrationNumber" END DESC,
        CASE WHEN p_SortColumn = 'CreatedAt' AND p_SortDirection = 'ASC' THEN sm."CreatedAt" END ASC,
        CASE WHEN p_SortColumn = 'CreatedAt' AND p_SortDirection = 'DESC' THEN sm."CreatedAt" END DESC,
        CASE WHEN p_SortColumn = 'Address' AND p_SortDirection = 'ASC' THEN sm."Address" END ASC,
        CASE WHEN p_SortColumn = 'Address' AND p_SortDirection = 'DESC' THEN sm."Address" END DESC,
        CASE WHEN p_SortColumn = 'Sequence' AND p_SortDirection = 'ASC' THEN sm."SchoolID" END ASC,
        CASE WHEN p_SortColumn = 'Sequence' AND p_SortDirection = 'DESC' THEN sm."SchoolID" END DESC,
        CASE WHEN p_SortColumn IS NULL AND p_SortDirection = 'DESC' THEN sm."SchoolID" END DESC
    LIMIT p_PageSize OFFSET v_Offset;
END;
$$ LANGUAGE plpgsql;


-- 4. Delete/Restore School
CREATE OR REPLACE FUNCTION "Proc_School_DeleteRestore"(
    p_SchoolID INT,
    p_Action VARCHAR, -- 'DELETE' or 'RESTORE'
    p_PerformedBy INT
) RETURNS JSON AS $$
DECLARE
    v_Success BOOLEAN := FALSE;
    v_Message VARCHAR := '';
    v_SchoolName VARCHAR;
BEGIN
    -- Get School Name for message
    SELECT "SchoolName" INTO v_SchoolName FROM "SchoolMaster" WHERE "SchoolID" = p_SchoolID;
    
    IF v_SchoolName IS NULL THEN
        RETURN json_build_object('success', FALSE, 'message', 'School not found');
    END IF;

    IF p_Action = 'DELETE' THEN
        UPDATE "SchoolMaster"
        SET "IsDeleted" = TRUE,
            "UpdatedBy" = p_PerformedBy,
            "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE "SchoolID" = p_SchoolID;
        
        v_Success := TRUE;
        v_Message := 'School soft deleted successfully';
    ELSIF p_Action = 'RESTORE' THEN
        UPDATE "SchoolMaster"
        SET "IsDeleted" = FALSE,
            "UpdatedBy" = p_PerformedBy,
            "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE "SchoolID" = p_SchoolID;
        
        v_Success := TRUE;
        v_Message := 'School restored successfully';
    ELSE
        v_Success := FALSE;
        v_Message := 'Invalid action';
    END IF;
    
    RETURN json_build_object('success', v_Success, 'message', v_Message);
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object('success', FALSE, 'message', SQLERRM);
END;
$$ LANGUAGE plpgsql;
