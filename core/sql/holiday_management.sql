-- Create HolidayMaster Table
CREATE TABLE IF NOT EXISTS "HolidayMaster" (
    "HolidayID" SERIAL PRIMARY KEY,
    "SchoolID" INT NOT NULL,
    "HolidayDate" DATE NOT NULL,
    "HolidayName" VARCHAR(200) NOT NULL,
    "HolidayType" VARCHAR(50) DEFAULT 'Public', -- 'Public', 'Weekly Off', 'School Event'
    "Description" TEXT,
    "IsRecurring" BOOLEAN DEFAULT FALSE,
    "IsDeleted" BOOLEAN DEFAULT FALSE,
    "CreatedBy" INT,
    "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "UpdatedBy" INT,
    "UpdatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for performance
CREATE INDEX IF NOT EXISTS "IDX_HolidayMaster_School_Date" ON "HolidayMaster" ("SchoolID", "HolidayDate");

-- Procedure for Listing Holidays
CREATE OR REPLACE FUNCTION "Proc_HolidayMaster_List"(
    p_school_id INT,
    p_year INT DEFAULT NULL,
    p_holiday_id INT DEFAULT NULL
)
RETURNS TABLE (
    "HolidayID" INT,
    "HolidayDate" DATE,
    "HolidayName" VARCHAR,
    "HolidayType" VARCHAR,
    "Description" TEXT,
    "IsRecurring" BOOLEAN,
    "SchoolID" INT,
    "SchoolName" VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        h."HolidayID",
        h."HolidayDate",
        h."HolidayName",
        h."HolidayType",
        h."Description",
        h."IsRecurring",
        h."SchoolID",
        s."SchoolName"
    FROM "HolidayMaster" h
    JOIN "SchoolMaster" s ON h."SchoolID" = s."SchoolID"
    WHERE h."IsDeleted" = FALSE
      AND (p_school_id IS NULL OR h."SchoolID" = p_school_id)
      AND (p_holiday_id IS NULL OR h."HolidayID" = p_holiday_id)
      AND (
          p_year IS NULL 
          OR h."IsRecurring" = TRUE 
          OR EXTRACT(YEAR FROM h."HolidayDate") = p_year
      )
    ORDER BY h."HolidayDate" ASC;
END;
$$ LANGUAGE plpgsql;

-- Procedure for Managing Holidays
CREATE OR REPLACE FUNCTION "Proc_HolidayMaster_Manage"(
    p_action VARCHAR, -- 'INSERT', 'UPDATE', 'DELETE', 'RESTORE'
    p_holiday_id INT,
    p_school_id INT,
    p_holiday_date DATE,
    p_holiday_name VARCHAR,
    p_holiday_type VARCHAR,
    p_description TEXT,
    p_is_recurring BOOLEAN,
    p_user_id INT
)
RETURNS INT AS $$
DECLARE
    v_id INT;
BEGIN
    IF p_action = 'INSERT' THEN
        INSERT INTO "HolidayMaster" (
            "SchoolID", "HolidayDate", "HolidayName", "HolidayType", "Description", "IsRecurring", "CreatedBy"
        ) VALUES (
            p_school_id, p_holiday_date, p_holiday_name, p_holiday_type, p_description, p_is_recurring, p_user_id
        ) RETURNING "HolidayID" INTO v_id;
    
    ELSIF p_action = 'UPDATE' THEN
        UPDATE "HolidayMaster" SET
            "HolidayDate" = p_holiday_date,
            "HolidayName" = p_holiday_name,
            "HolidayType" = p_holiday_type,
            "Description" = p_description,
            "IsRecurring" = p_is_recurring,
            "UpdatedBy" = p_user_id,
            "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE "HolidayID" = p_holiday_id;
        v_id := p_holiday_id;
        
    ELSIF p_action = 'DELETE' THEN
        UPDATE "HolidayMaster" SET "IsDeleted" = TRUE, "UpdatedBy" = p_user_id, "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE "HolidayID" = p_holiday_id;
        v_id := p_holiday_id;
        
    ELSIF p_action = 'RESTORE' THEN
        UPDATE "HolidayMaster" SET "IsDeleted" = FALSE, "UpdatedBy" = p_user_id, "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE "HolidayID" = p_holiday_id;
        v_id := p_holiday_id;
    END IF;
    
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- Procedure for Bulk Weekly Off Generation
CREATE OR REPLACE FUNCTION "Proc_HolidayMaster_BulkGenerate"(
    p_school_id INT,
    p_start_date DATE,
    p_end_date DATE,
    p_day_of_week INT, -- 0 for Sunday
    p_user_id INT
)
RETURNS INT AS $$
DECLARE
    curr_date DATE := p_start_date;
    count INT := 0;
BEGIN
    WHILE curr_date <= p_end_date LOOP
        IF EXTRACT(DOW FROM curr_date) = p_day_of_week THEN
            -- Check if already exists
            IF NOT EXISTS (
                SELECT 1 FROM "HolidayMaster" 
                WHERE "SchoolID" = p_school_id 
                AND "HolidayDate" = curr_date 
                AND "IsDeleted" = FALSE
            ) THEN
                INSERT INTO "HolidayMaster" (
                    "SchoolID", "HolidayDate", "HolidayName", "HolidayType", "IsRecurring", "CreatedBy"
                ) VALUES (
                    p_school_id, curr_date, 'Weekly Off', 'Weekly Off', FALSE, p_user_id
                );
                count := count + 1;
            END IF;
        END IF;
        curr_date := curr_date + 1;
    END LOOP;
    RETURN count;
END;
$$ LANGUAGE plpgsql;
