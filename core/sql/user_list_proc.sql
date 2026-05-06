CREATE OR REPLACE FUNCTION "Proc_UserList_Get"(
    p_PageNumber INT,
    p_PageSize INT,
    p_UserID INT,
    p_ProfileID INT,
    p_SchoolID INT,
    p_SearchTerm TEXT,
    p_FromDate TIMESTAMP,
    p_ToDate TIMESTAMP,
    p_Status TEXT,
    p_OrderBy TEXT,
    p_OrderDirection TEXT
)
RETURNS TABLE (
    "UserID" INT,
    "UserCode" VARCHAR,
    "UserName" VARCHAR,
    "Email" VARCHAR,
    "Phone" VARCHAR,
    "ProfileID" INT,
    "ProfileName" VARCHAR,
    "SchoolID" INT,
    "SchoolName" VARCHAR,
    "UserPhoto" BYTEA,
    "IsDeleted" INT,
    "CreatedAt" TIMESTAMP,
    "TotalCount" BIGINT
) AS $$
DECLARE
    v_sql TEXT;
    v_offset INT;
BEGIN
    v_offset := (p_PageNumber - 1) * p_PageSize;
    
    v_sql := '
        SELECT 
            u."UserID",
            u."UserCode",
            u."UserName",
            u."Email",
            u."Phone",
            u."ProfileID",
            p."ProfileName",
            u."SchoolID",
            s."SchoolName",
            u."UserPhoto",
            CASE WHEN u."IsDeleted" THEN 1 ELSE 0 END as "IsDeleted",
            u."CreatedAt",
            COUNT(*) OVER() as "TotalCount"
        FROM "UserMaster" u
        LEFT JOIN "ProfileMaster" p ON u."ProfileID" = p."ProfileID"
        LEFT JOIN "SchoolMaster" s ON u."SchoolID" = s."SchoolID"
        WHERE 1=1';

    -- Filter by ProfileID
    IF p_ProfileID IS NOT NULL AND p_ProfileID > 0 THEN
        v_sql := v_sql || ' AND u."ProfileID" = ' || p_ProfileID;
    END IF;

    -- Filter by SchoolID
    IF p_SchoolID IS NOT NULL AND p_SchoolID > 0 THEN
        v_sql := v_sql || ' AND u."SchoolID" = ' || p_SchoolID;
    END IF;

    -- Filter by Status (Active/Inactive)
    IF p_Status IS NOT NULL AND p_Status <> '' THEN
        IF p_Status = 'Active' THEN
            v_sql := v_sql || ' AND u."IsDeleted" = FALSE';
        ELSIF p_Status = 'Inactive' THEN
            v_sql := v_sql || ' AND u."IsDeleted" = TRUE';
        END IF;
    END IF;

    -- Filter by SearchTerm
    IF p_SearchTerm IS NOT NULL AND p_SearchTerm <> '' THEN
        v_sql := v_sql || ' AND (
            u."UserName" ILIKE ' || quote_literal('%' || p_SearchTerm || '%') || ' OR 
            u."UserCode" ILIKE ' || quote_literal('%' || p_SearchTerm || '%') || ' OR 
            u."Email" ILIKE ' || quote_literal('%' || p_SearchTerm || '%') || ' OR 
            u."Phone" ILIKE ' || quote_literal('%' || p_SearchTerm || '%') || '
        )';
    END IF;

    -- Filter by Dates
    IF p_FromDate IS NOT NULL THEN
        v_sql := v_sql || ' AND u."CreatedAt" >= ' || quote_literal(p_FromDate::TEXT);
    END IF;

    IF p_ToDate IS NOT NULL THEN
        v_sql := v_sql || ' AND u."CreatedAt" <= ' || quote_literal(p_ToDate::TEXT);
    END IF;

    -- Dynamic Sorting
    v_sql := v_sql || ' ORDER BY ' || 
        CASE 
            WHEN p_OrderBy = 'UserCode' THEN 'u."UserCode"'
            WHEN p_OrderBy = 'UserName' THEN 'u."UserName"'
            WHEN p_OrderBy = 'Email' THEN 'u."Email"'
            WHEN p_OrderBy = 'Phone' THEN 'u."Phone"'
            WHEN p_OrderBy = 'ProfileID' THEN 'u."ProfileID"'
            WHEN p_OrderBy = 'SchoolID' THEN 'u."SchoolID"'
            WHEN p_OrderBy = 'CreatedAt' THEN 'u."CreatedAt"'
            ELSE 'u."CreatedAt"'
        END;

    IF p_OrderDirection ILIKE 'DESC' THEN
        v_sql := v_sql || ' DESC';
    ELSE
        v_sql := v_sql || ' ASC';
    END IF;

    -- Pagination
    v_sql := v_sql || ' LIMIT ' || p_PageSize || ' OFFSET ' || v_offset;

    RETURN QUERY EXECUTE v_sql;
END;
$$ LANGUAGE plpgsql;
