from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Setup PostgreSQL functions for Teachers & Staff module'

    def handle(self, *args, **options):
        self.stdout.write('Setting up Teachers & Staff PostgreSQL functions...')

        procedures = [
            """
            -- Proc_Add_Staff_Profile_Role_Get
            CREATE OR REPLACE FUNCTION "Proc_Add_Staff_Profile_Role_Get"()
            RETURNS TABLE (
                "ProfileID" INT,
                "ProfileName" VARCHAR
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT p."ProfileID", p."ProfileName"
                FROM "ProfileMaster" p
                WHERE p."ProfileName" IN ('Teacher', 'Accountant', 'Librarian', 'Driver', 'Support Executive', 'School Admin')
                AND COALESCE(p."IsDeleted", false) = false
                ORDER BY p."ProfileName";
            END;
            $$ LANGUAGE plpgsql;
            """,

            """
            -- Proc_Check_NationalID
            CREATE OR REPLACE FUNCTION "Proc_Check_NationalID"(
                p_NationalID VARCHAR,
                p_SchoolID INT
            )
            RETURNS TABLE (
                "Count" BIGINT
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT COUNT(*)
                FROM "EmployeeMaster"
                WHERE "NationalID" = p_NationalID 
                AND "SchoolID" = p_SchoolID 
                AND "IsDeleted" = false;
            END;
            $$ LANGUAGE plpgsql;
            """,

            """
            -- Proc_Executive_set (Add Employee)
            CREATE OR REPLACE FUNCTION "Proc_Executive_set"(
                p_SchoolID INT,
                p_EmployeeName VARCHAR,
                p_MobileNo VARCHAR,
                p_Email VARCHAR,
                p_Password VARCHAR,
                p_DateOfBirth DATE,
                p_ProfileId INT,
                p_DateOfJoining DATE,
                p_FatherOrHusbandName VARCHAR,
                p_NationalID VARCHAR,
                p_Gender VARCHAR,
                p_Religion VARCHAR,
                p_Education VARCHAR,
                p_BloodGroup VARCHAR,
                p_Country VARCHAR,
                p_State VARCHAR,
                p_District VARCHAR,
                p_Pincode VARCHAR,
                p_HomeAddress VARCHAR,
                p_Experience VARCHAR,
                p_EmploymentType VARCHAR,
                p_CreatedBy INT,
                p_SalaryComponents JSONB,
                p_DocumentComponents JSONB
            )
            RETURNS TABLE (
                "ResultJson" TEXT,
                "UserCode" VARCHAR
            ) AS $$
            DECLARE
                v_EmployeeID INT;
                v_EmployeeCode VARCHAR;
                v_MaxEmployeeID INT;
                v_Status VARCHAR;
                v_Message VARCHAR;
                v_SalaryRec RECORD;
                v_DocRec RECORD;
            BEGIN
                -- Validate required fields
                IF p_SchoolID IS NULL OR p_SchoolID = 0 THEN
                    RETURN QUERY SELECT '{"Status":"FAILED","Message":"School ID is required"}'::TEXT, NULL::VARCHAR;
                    RETURN;
                END IF;

                IF p_EmployeeName IS NULL OR TRIM(p_EmployeeName) = '' THEN
                    RETURN QUERY SELECT '{"Status":"FAILED","Message":"Employee name is required"}'::TEXT, NULL::VARCHAR;
                    RETURN;
                END IF;

                -- Check National ID
                IF p_NationalID IS NOT NULL AND p_NationalID != '' THEN
                    IF EXISTS (SELECT 1 FROM "EmployeeMaster" WHERE "NationalID" = p_NationalID AND "SchoolID" = p_SchoolID AND "IsDeleted" = false) THEN
                        RETURN QUERY SELECT '{"Status":"FAILED","Message":"National ID already exists in the system"}'::TEXT, NULL::VARCHAR;
                        RETURN;
                    END IF;
                END IF;

                -- Generate Employee Code
                SELECT COALESCE(MAX("EmployeeID"), 0) INTO v_MaxEmployeeID FROM "EmployeeMaster";
                v_EmployeeCode := 'EMP' || LPAD((v_MaxEmployeeID + 1)::TEXT, 6, '0');

                -- Insert into EmployeeMaster
                INSERT INTO "EmployeeMaster" (
                    "SchoolID", "EmployeeCode", "EmployeeName", "MobileNo", "Email", "Password",
                    "DateOfBirth", "ProfileId", "DateOfJoining", "FatherOrHusbandName", "NationalID",
                    "Gender", "Religion", "Education", "BloodGroup", "Country", "State", "District",
                    "Pincode", "HomeAddress", "Experience", "EmploymentType",
                    "CreatedBy", "CreatedAt", "IsDeleted"
                )
                VALUES (
                    p_SchoolID, v_EmployeeCode, p_EmployeeName, p_MobileNo, p_Email, p_Password,
                    p_DateOfBirth, p_ProfileId, p_DateOfJoining, p_FatherOrHusbandName, p_NationalID,
                    p_Gender, p_Religion, p_Education, p_BloodGroup, p_Country, p_State, p_District,
                    p_Pincode, p_HomeAddress, p_Experience, p_EmploymentType,
                    p_CreatedBy, CURRENT_TIMESTAMP, false
                )
                RETURNING "EmployeeID" INTO v_EmployeeID;

                -- Process Salary Components
                IF p_SalaryComponents IS NOT NULL THEN
                    FOR v_SalaryRec IN SELECT * FROM jsonb_to_recordset(p_SalaryComponents) AS x("ComponentID" INT, "Amount" DECIMAL)
                    LOOP
                        IF v_SalaryRec."Amount" > 0 THEN
                            INSERT INTO "EmployeeSalaryBreakup" (
                                "EmployeeID", "SchoolID", "ComponentID", "Amount", "CreatedBy", "CreatedAt", "IsDeleted"
                            )
                            VALUES (
                                v_EmployeeID, p_SchoolID, v_SalaryRec."ComponentID", v_SalaryRec."Amount", p_CreatedBy, CURRENT_TIMESTAMP, false
                            );
                        END IF;
                    END LOOP;
                END IF;

                -- Process Documents
                IF p_DocumentComponents IS NOT NULL THEN
                    FOR v_DocRec IN SELECT * FROM jsonb_to_recordset(p_DocumentComponents) AS x("DocumentType" VARCHAR, "FilesName" VARCHAR, "FileExtension" VARCHAR, "FileContent" TEXT)
                    LOOP
                        INSERT INTO "EmployeeDocument" (
                            "EmployeeID", "DocumentType", "FilesName", "FileExtension", "FileContent", "UploadedBy", "UploadedAt", "IsActive", "IsDeleted"
                        )
                        VALUES (
                            v_EmployeeID,
                            v_DocRec."DocumentType",
                            v_DocRec."FilesName",
                            v_DocRec."FileExtension",
                            decode(v_DocRec."FileContent", 'base64'),
                            p_CreatedBy,
                            CURRENT_TIMESTAMP,
                            true,
                            false
                        );
                    END LOOP;
                END IF;

                v_Status := 'SUCCESS';
                v_Message := 'Employee added successfully';

                RETURN QUERY SELECT 
                    jsonb_build_object(
                        'Status', v_Status,
                        'Message', v_Message,
                        'EmployeeID', v_EmployeeID,
                        'EmployeeCode', v_EmployeeCode,
                        'Position', (SELECT "ProfileName" FROM "ProfileMaster" WHERE "ProfileID" = p_ProfileId),
                        'Username', p_Email
                    )::TEXT,
                    v_EmployeeCode;

            EXCEPTION WHEN OTHERS THEN
                RETURN QUERY SELECT 
                    jsonb_build_object(
                        'Status', 'FAILED',
                        'Message', SQLERRM
                    )::TEXT,
                    NULL::VARCHAR;
            END;
            $$ LANGUAGE plpgsql;
            """,

            """
            -- Proc_Employee_List
            CREATE OR REPLACE FUNCTION "Proc_Employee_List"(
                p_SchoolID INT,
                p_LoggedInUserID INT,
                p_LoggedInProfileID INT,
                p_EmployeeCode VARCHAR DEFAULT NULL,
                p_ProfileName VARCHAR DEFAULT NULL,
                p_MobileNo VARCHAR DEFAULT NULL,
                p_Email VARCHAR DEFAULT NULL,
                p_Country VARCHAR DEFAULT NULL,
                p_State VARCHAR DEFAULT NULL,
                p_District VARCHAR DEFAULT NULL,
                p_Pincode VARCHAR DEFAULT NULL,
                p_Religion VARCHAR DEFAULT NULL,
                p_NationalID VARCHAR DEFAULT NULL,
                p_Gender VARCHAR DEFAULT NULL,
                p_EmployeeName VARCHAR DEFAULT NULL,
                p_Status VARCHAR DEFAULT NULL,
                p_CreatedFrom DATE DEFAULT NULL,
                p_CreatedTo DATE DEFAULT NULL,
                p_OrderBy VARCHAR DEFAULT 'EmployeeCode',
                p_OrderDirection VARCHAR DEFAULT 'ASC',
                p_PageNumber INT DEFAULT 1,
                p_PageSize INT DEFAULT 25
            )
            RETURNS TABLE (
                "EmployeeID" INT,
                "EmployeeCode" VARCHAR,
                "EmployeeName" VARCHAR,
                "MobileNo" VARCHAR,
                "Email" VARCHAR,
                "ProfileName" VARCHAR,
                "DateOfJoining" DATE,
                "Status" VARCHAR,
                "TotalCount" BIGINT
            ) AS $$
            DECLARE
                v_Offset INT;
            BEGIN
                v_Offset := (p_PageNumber - 1) * p_PageSize;

                RETURN QUERY
                WITH FilteredEmployees AS (
                    SELECT 
                        e."EmployeeID",
                        e."EmployeeCode",
                        e."EmployeeName",
                        e."MobileNo",
                        e."Email",
                        p."ProfileName",
                        e."DateOfJoining",
                        CASE WHEN e."IsDeleted" = false THEN 'Active' ELSE 'Inactive' END AS "Status"
                    FROM "EmployeeMaster" e
                    LEFT JOIN "ProfileMaster" p ON e."ProfileId" = p."ProfileID"
                    WHERE e."SchoolID" = p_SchoolID
                    AND (p_EmployeeCode IS NULL OR e."EmployeeCode" ILIKE '%' || p_EmployeeCode || '%')
                    AND (p_EmployeeName IS NULL OR e."EmployeeName" ILIKE '%' || p_EmployeeName || '%')
                    AND (p_MobileNo IS NULL OR e."MobileNo" ILIKE '%' || p_MobileNo || '%')
                    AND (p_Email IS NULL OR e."Email" ILIKE '%' || p_Email || '%')
                    AND (p_ProfileName IS NULL OR p."ProfileName" ILIKE '%' || p_ProfileName || '%')
                    AND (p_Country IS NULL OR e."Country" ILIKE '%' || p_Country || '%')
                    AND (p_State IS NULL OR e."State" ILIKE '%' || p_State || '%')
                    AND (p_District IS NULL OR e."District" ILIKE '%' || p_District || '%')
                    AND (p_Pincode IS NULL OR e."Pincode" ILIKE '%' || p_Pincode || '%')
                    AND (p_Religion IS NULL OR e."Religion" ILIKE '%' || p_Religion || '%')
                    AND (p_NationalID IS NULL OR e."NationalID" ILIKE '%' || p_NationalID || '%')
                    AND (p_Gender IS NULL OR e."Gender" = p_Gender)
                    AND (p_Status IS NULL OR 
                        (p_Status = 'Active' AND e."IsDeleted" = false) OR 
                        (p_Status = 'Inactive' AND e."IsDeleted" = true))
                    AND (p_CreatedFrom IS NULL OR e."DateOfJoining" >= p_CreatedFrom)
                    AND (p_CreatedTo IS NULL OR e."DateOfJoining" <= p_CreatedTo)
                ),
                Total AS (
                    SELECT COUNT(*) AS "Count" FROM FilteredEmployees
                )
                SELECT 
                    fe."EmployeeID",
                    fe."EmployeeCode",
                    fe."EmployeeName",
                    fe."MobileNo",
                    fe."Email",
                    fe."ProfileName",
                    fe."DateOfJoining",
                    fe."Status"::VARCHAR,
                    t."Count"
                FROM FilteredEmployees fe
                CROSS JOIN Total t
                ORDER BY
                    CASE WHEN p_OrderBy = 'EmployeeCode' AND p_OrderDirection = 'ASC' THEN fe."EmployeeCode" END ASC,
                    CASE WHEN p_OrderBy = 'EmployeeCode' AND p_OrderDirection = 'DESC' THEN fe."EmployeeCode" END DESC,
                    CASE WHEN p_OrderBy = 'EmployeeName' AND p_OrderDirection = 'ASC' THEN fe."EmployeeName" END ASC,
                    CASE WHEN p_OrderBy = 'EmployeeName' AND p_OrderDirection = 'DESC' THEN fe."EmployeeName" END DESC,
                    CASE WHEN p_OrderBy = 'DateOfJoining' AND p_OrderDirection = 'ASC' THEN fe."DateOfJoining" END ASC,
                    CASE WHEN p_OrderBy = 'DateOfJoining' AND p_OrderDirection = 'DESC' THEN fe."DateOfJoining" END DESC
                LIMIT p_PageSize OFFSET v_Offset;
            END;
            $$ LANGUAGE plpgsql;
            """,

            """
            -- Proc_Employee_Detail_Get
            CREATE OR REPLACE FUNCTION "Proc_Employee_Detail_Get"(
                p_EmployeeCode VARCHAR,
                p_SchoolID INT
            )
            RETURNS TABLE (
                "EmployeeData" JSONB,
                "SalaryData" JSONB,
                "DocumentData" JSONB
            ) AS $$
            DECLARE
                v_EmployeeID INT;
                v_EmployeeData JSONB;
                v_SalaryData JSONB;
                v_DocumentData JSONB;
            BEGIN
                -- Get Employee ID
                SELECT "EmployeeID" INTO v_EmployeeID 
                FROM "EmployeeMaster" 
                WHERE "EmployeeCode" = p_EmployeeCode AND "SchoolID" = p_SchoolID;

                -- Get Employee Info
                SELECT jsonb_build_object(
                    'EmployeeID', e."EmployeeID",
                    'EmployeeCode', e."EmployeeCode",
                    'EmployeeName', e."EmployeeName",
                    'Gender', e."Gender",
                    'DateOfBirth', e."DateOfBirth",
                    'DateOfJoining', e."DateOfJoining",
                    'MobileNo', e."MobileNo",
                    'Email', e."Email",
                    'FatherOrHusbandName', e."FatherOrHusbandName",
                    'NationalID', e."NationalID",
                    'Religion', e."Religion",
                    'Education', e."Education",
                    'BloodGroup', e."BloodGroup",
                    'Experience', e."Experience",
                    'ProfileName', p."ProfileName",
                    'HomeAddress', e."HomeAddress",
                    'Country', e."Country",
                    'State', e."State",
                    'District', e."District",
                    'Pincode', e."Pincode",
                    'EmploymentType', e."EmploymentType",
                    'CreatedBy', u."UserName",
                    'CreatedAt', e."CreatedAt",
                    'Status', CASE WHEN e."IsDeleted" = false THEN 'Active' ELSE 'Inactive' END,
                    'CoreSubjects', (
                        SELECT string_agg(sm."SubjectName", ', ')
                        FROM "EmployeeCoreSubjects" ecs
                        JOIN "SubjectMaster" sm ON ecs."SubjectID" = sm."SubjectID"
                        WHERE ecs."EmployeeID" = e."EmployeeID"
                    )
                ) INTO v_EmployeeData
                FROM "EmployeeMaster" e
                LEFT JOIN "ProfileMaster" p ON e."ProfileId" = p."ProfileID"
                LEFT JOIN "UserMaster" u ON u."UserID" = e."CreatedBy"
                WHERE e."EmployeeID" = v_EmployeeID;

                -- Get Salary Breakup
                SELECT jsonb_agg(jsonb_build_object(
                    'EmployeeID', esb."EmployeeID",
                    'ComponentID', esb."ComponentID",
                    'ComponentType', sc."ComponentType",
                    'ComponentName', sc."ComponentName",
                    'Amount', esb."Amount"
                )) INTO v_SalaryData
                FROM "EmployeeSalaryBreakup" esb
                INNER JOIN "SalaryComponentMaster" sc ON esb."ComponentID" = sc."ComponentID"
                WHERE esb."EmployeeID" = v_EmployeeID;

                -- Get Documents
                SELECT jsonb_agg(jsonb_build_object(
                    'DocumentID', ed."DocumentID",
                    'EmployeeID', ed."EmployeeID",
                    'DocumentType', ed."DocumentType",
                    'FilesName', ed."FilesName",
                    'FileExtension', ed."FileExtension",
                    'FileContent', encode(ed."FileContent", 'base64')
                )) INTO v_DocumentData
                FROM "EmployeeDocument" ed
                WHERE ed."EmployeeID" = v_EmployeeID AND ed."IsDeleted" = false;

                RETURN QUERY SELECT 
                    COALESCE(v_EmployeeData, '{}'::jsonb),
                    COALESCE(v_SalaryData, '[]'::jsonb),
                    COALESCE(v_DocumentData, '[]'::jsonb);
            END;
            $$ LANGUAGE plpgsql;
            """,

            """
            -- Proc_Employee_Personal_Update
            CREATE OR REPLACE FUNCTION "Proc_Employee_Personal_Update"(
                p_EmployeeCode VARCHAR,
                p_SchoolID INT,
                p_EmployeeName VARCHAR,
                p_Gender VARCHAR,
                p_DateOfBirth DATE,
                p_DateOfJoining DATE,
                p_FatherOrHusbandName VARCHAR,
                p_NationalID VARCHAR,
                p_Religion VARCHAR,
                p_Education VARCHAR,
                p_BloodGroup VARCHAR,
                p_Experience VARCHAR,
                p_EmploymentType VARCHAR,
                p_UpdatedBy INT
            )
            RETURNS TABLE (
                "Status" VARCHAR,
                "Message" VARCHAR
            ) AS $$
            DECLARE
                v_EmployeeID INT;
            BEGIN
                SELECT "EmployeeID" INTO v_EmployeeID 
                FROM "EmployeeMaster" 
                WHERE "EmployeeCode" = p_EmployeeCode AND "SchoolID" = p_SchoolID;

                IF v_EmployeeID IS NULL THEN
                    RETURN QUERY SELECT 'error'::VARCHAR, 'Employee not found'::VARCHAR;
                    RETURN;
                END IF;

                UPDATE "EmployeeMaster"
                SET 
                    "EmployeeName" = COALESCE(p_EmployeeName, "EmployeeName"),
                    "Gender" = COALESCE(p_Gender, "Gender"),
                    "DateOfBirth" = COALESCE(p_DateOfBirth, "DateOfBirth"),
                    "DateOfJoining" = COALESCE(p_DateOfJoining, "DateOfJoining"),
                    "FatherOrHusbandName" = COALESCE(p_FatherOrHusbandName, "FatherOrHusbandName"),
                    "NationalID" = COALESCE(p_NationalID, "NationalID"),
                    "Religion" = COALESCE(p_Religion, "Religion"),
                    "Education" = COALESCE(p_Education, "Education"),
                    "BloodGroup" = COALESCE(p_BloodGroup, "BloodGroup"),
                    "Experience" = COALESCE(p_Experience, "Experience"),
                    "EmploymentType" = COALESCE(p_EmploymentType, "EmploymentType"),
                    "UpdatedBy" = p_UpdatedBy,
                    "UpdatedAt" = CURRENT_TIMESTAMP
                WHERE "EmployeeID" = v_EmployeeID;

                RETURN QUERY SELECT 'success'::VARCHAR, 'Personal information updated successfully'::VARCHAR;
            END;
            $$ LANGUAGE plpgsql;
            """,

            """
            -- Proc_Employee_Contact_Update
            CREATE OR REPLACE FUNCTION "Proc_Employee_Contact_Update"(
                p_EmployeeCode VARCHAR,
                p_SchoolID INT,
                p_MobileNo VARCHAR,
                p_Email VARCHAR,
                p_HomeAddress VARCHAR,
                p_Country VARCHAR,
                p_State VARCHAR,
                p_District VARCHAR,
                p_Pincode VARCHAR,
                p_UpdatedBy INT
            )
            RETURNS TABLE (
                "Status" VARCHAR,
                "Message" VARCHAR
            ) AS $$
            DECLARE
                v_EmployeeID INT;
            BEGIN
                SELECT "EmployeeID" INTO v_EmployeeID 
                FROM "EmployeeMaster" 
                WHERE "EmployeeCode" = p_EmployeeCode AND "SchoolID" = p_SchoolID;

                IF v_EmployeeID IS NULL THEN
                    RETURN QUERY SELECT 'error'::VARCHAR, 'Employee not found'::VARCHAR;
                    RETURN;
                END IF;

                UPDATE "EmployeeMaster"
                SET 
                    "MobileNo" = COALESCE(p_MobileNo, "MobileNo"),
                    "Email" = COALESCE(p_Email, "Email"),
                    "HomeAddress" = COALESCE(p_HomeAddress, "HomeAddress"),
                    "Country" = COALESCE(p_Country, "Country"),
                    "State" = COALESCE(p_State, "State"),
                    "District" = COALESCE(p_District, "District"),
                    "Pincode" = COALESCE(p_Pincode, "Pincode"),
                    "UpdatedBy" = p_UpdatedBy,
                    "UpdatedAt" = CURRENT_TIMESTAMP
                WHERE "EmployeeID" = v_EmployeeID;

                RETURN QUERY SELECT 'success'::VARCHAR, 'Contact information updated successfully'::VARCHAR;
            END;
            $$ LANGUAGE plpgsql;
            """,

            """
            -- Proc_Employee_Salary_Update
            CREATE OR REPLACE FUNCTION "Proc_Employee_Salary_Update"(
                p_EmployeeCode VARCHAR,
                p_SchoolID INT,
                p_SalaryData JSONB,
                p_UpdatedBy INT
            )
            RETURNS TABLE (
                "Status" VARCHAR,
                "Message" VARCHAR
            ) AS $$
            DECLARE
                v_EmployeeID INT;
                v_SalaryRec RECORD;
            BEGIN
                SELECT "EmployeeID" INTO v_EmployeeID 
                FROM "EmployeeMaster" 
                WHERE "EmployeeCode" = p_EmployeeCode AND "SchoolID" = p_SchoolID;

                IF v_EmployeeID IS NULL THEN
                    RETURN QUERY SELECT 'error'::VARCHAR, 'Employee not found'::VARCHAR;
                    RETURN;
                END IF;

                IF p_SalaryData IS NOT NULL THEN
                    FOR v_SalaryRec IN SELECT * FROM jsonb_to_recordset(p_SalaryData) AS x("ComponentID" INT, "Amount" DECIMAL)
                    LOOP
                        IF EXISTS (SELECT 1 FROM "EmployeeSalaryBreakup" WHERE "EmployeeID" = v_EmployeeID AND "ComponentID" = v_SalaryRec."ComponentID") THEN
                            UPDATE "EmployeeSalaryBreakup"
                            SET "Amount" = v_SalaryRec."Amount",
                                "UpdatedBy" = p_UpdatedBy,
                                "UpdatedAt" = CURRENT_TIMESTAMP
                            WHERE "EmployeeID" = v_EmployeeID AND "ComponentID" = v_SalaryRec."ComponentID";
                        ELSE
                            INSERT INTO "EmployeeSalaryBreakup" ("EmployeeID", "SchoolID", "ComponentID", "Amount", "CreatedBy", "CreatedAt")
                            VALUES (v_EmployeeID, p_SchoolID, v_SalaryRec."ComponentID", v_SalaryRec."Amount", p_UpdatedBy, CURRENT_TIMESTAMP);
                        END IF;
                    END LOOP;
                END IF;

                RETURN QUERY SELECT 'success'::VARCHAR, 'Salary breakup updated successfully'::VARCHAR;
            END;
            $$ LANGUAGE plpgsql;
            """,

            """
            -- Proc_Employee_Document_Update
            CREATE OR REPLACE FUNCTION "Proc_Employee_Document_Update"(
                p_EmployeeCode VARCHAR,
                p_SchoolID INT,
                p_DocumentType VARCHAR,
                p_FileName VARCHAR,
                p_FileExtension VARCHAR,
                p_FileContent BYTEA,
                p_UpdatedBy INT
            )
            RETURNS TABLE (
                "Status" VARCHAR,
                "Message" VARCHAR
            ) AS $$
            DECLARE
                v_EmployeeID INT;
                v_ExistingDocID INT;
            BEGIN
                SELECT "EmployeeID" INTO v_EmployeeID 
                FROM "EmployeeMaster" 
                WHERE "EmployeeCode" = p_EmployeeCode AND "SchoolID" = p_SchoolID;

                IF v_EmployeeID IS NULL THEN
                    RETURN QUERY SELECT 'error'::VARCHAR, 'Employee not found'::VARCHAR;
                    RETURN;
                END IF;

                SELECT "DocumentID" INTO v_ExistingDocID 
                FROM "EmployeeDocument" 
                WHERE "EmployeeID" = v_EmployeeID AND "DocumentType" = p_DocumentType;

                IF v_ExistingDocID IS NOT NULL THEN
                    UPDATE "EmployeeDocument"
                    SET "FilesName" = p_FileName,
                        "FileExtension" = p_FileExtension,
                        "FileContent" = p_FileContent,
                        "UploadedBy" = p_UpdatedBy,
                        "UploadedAt" = CURRENT_TIMESTAMP,
                        "IsActive" = true,
                        "IsDeleted" = false
                    WHERE "DocumentID" = v_ExistingDocID;
                    
                    RETURN QUERY SELECT 'success'::VARCHAR, 'Document updated successfully'::VARCHAR;
                ELSE
                    INSERT INTO "EmployeeDocument" ("EmployeeID", "DocumentType", "FilesName", "FileExtension", "FileContent", "UploadedBy", "UploadedAt", "IsActive", "IsDeleted")
                    VALUES (v_EmployeeID, p_DocumentType, p_FileName, p_FileExtension, p_FileContent, p_UpdatedBy, CURRENT_TIMESTAMP, true, false);
                    
                    RETURN QUERY SELECT 'success'::VARCHAR, 'Document uploaded successfully'::VARCHAR;
                END IF;
            END;
            $$ LANGUAGE plpgsql;
            """,

            """
            -- Proc_AssignClasses_PageLoad (Helper to get all dropdown data in one call)
            CREATE OR REPLACE FUNCTION "Proc_AssignClasses_PageLoad"(
                p_SchoolID INT
            )
            RETURNS TABLE (
                "Teachers" JSONB,
                "AcademicYears" JSONB,
                "Classes" JSONB,
                "Sections" JSONB,
                "Subjects" JSONB
            ) AS $$
            DECLARE
                v_Teachers JSONB;
                v_AcademicYears JSONB;
                v_Classes JSONB;
                v_Sections JSONB;
                v_Subjects JSONB;
            BEGIN
                -- Teachers (Include all employees of the school)
                SELECT jsonb_agg(jsonb_build_object(
                    'TeacherId', e."EmployeeID",
                    'EmployeeCode', e."EmployeeCode",
                    'TeacherName', e."EmployeeName"
                )) INTO v_Teachers
                FROM "EmployeeMaster" e
                WHERE e."IsDeleted" = false
                AND e."SchoolID" = p_SchoolID;

                -- Academic Years
                SELECT jsonb_agg(jsonb_build_object(
                    'id', a."AcademicYearID",
                    'name', a."AcademicYear"
                )) INTO v_AcademicYears
                FROM "AcademicYear" a
                WHERE a."SchoolID" = p_SchoolID;

                -- Classes
                SELECT jsonb_agg(jsonb_build_object(
                    'id', c."ClassID",
                    'name', c."ClassName"
                )) INTO v_Classes
                FROM "ClassMaster" c
                WHERE c."SchoolID" = p_SchoolID
                ORDER BY c."ClassID";

                -- Sections (Grouped by ClassID handled in view, here we return flat list efficiently)
                SELECT jsonb_agg(jsonb_build_object(
                    'id', s."SectionID",
                    'name', s."SectionName",
                    'class_id', s."ClassID"
                )) INTO v_Sections
                FROM "SectionMaster" s
                JOIN "ClassMaster" c ON s."ClassID" = c."ClassID"
                WHERE c."SchoolID" = p_SchoolID;

                -- Subjects
                SELECT jsonb_agg(jsonb_build_object(
                    'SubjectID', sub."SubjectID",
                    'SubjectCode', sub."SubjectCode",
                    'SubjectName', sub."SubjectName",
                    'ClassId', sub."ClassId"
                )) INTO v_Subjects
                FROM "SubjectMaster" sub
                WHERE sub."SchoolID" = p_SchoolID AND sub."IsDeleted" = false;

                RETURN QUERY SELECT 
                    COALESCE(v_Teachers, '[]'::jsonb),
                    COALESCE(v_AcademicYears, '[]'::jsonb),
                    COALESCE(v_Classes, '[]'::jsonb),
                    COALESCE(v_Sections, '[]'::jsonb),
                    COALESCE(v_Subjects, '[]'::jsonb);
            END;
            $$ LANGUAGE plpgsql;
            """,
            
            """
            -- Proc_Check_Class_Teacher_Conflict
            CREATE OR REPLACE FUNCTION "Proc_Check_Class_Teacher_Conflict"(
                p_TeacherID INT,
                p_AcademicYear VARCHAR,
                p_SchoolID INT,
                p_ClassID INT
            )
            RETURNS TABLE (
                "ConflictCount" BIGINT,
                "ConflictClassName" VARCHAR,
                "StartDate" DATE,
                "EndDate" DATE
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    COUNT(*) AS "ConflictCount",
                    MAX(tc."ClassName") AS "ConflictClassName",
                    MAX(tcs."StartDate") AS "StartDate",
                    MAX(tcs."EndDate") AS "EndDate"
                FROM "TeacherClassAssignment" tcs
                JOIN "ClassMaster" tc ON tcs."ClassID" = tc."ClassID"
                WHERE tcs."TeacherID" = p_TeacherID
                AND tcs."AcademicYear" = p_AcademicYear
                AND tcs."SchoolID" = p_SchoolID
                AND tcs."IsClassTeacher" = 1
                AND tcs."ClassID" != p_ClassID;
            END;
            $$ LANGUAGE plpgsql;
            """,
            
            """
            -- Proc_AssignTeacherToClass_set
            CREATE OR REPLACE FUNCTION "Proc_AssignTeacherToClass_set"(
                p_AssignmentID INT,
                p_SchoolID INT,
                p_TeacherID INT,
                p_ClassID INT,
                p_SectionID INT,
                p_SubjectID INT,
                p_AcademicYear VARCHAR,
                p_StartDate DATE,
                p_EndDate DATE,
                p_IsClassTeacher BOOLEAN,
                p_AssignmentOrder INT,
                p_Remarks VARCHAR,
                p_Action VARCHAR,
                p_CreatedBy INT
            )
            RETURNS TABLE (
                "Status" VARCHAR,
                "Message" VARCHAR
            ) AS $$
            DECLARE
                v_ConflictCount INT;
            BEGIN
                -- Check Conflict if Class Teacher
                IF p_IsClassTeacher = true THEN
                     SELECT COUNT(*) INTO v_ConflictCount
                     FROM "TeacherClassAssignment"
                     WHERE "TeacherID" = p_TeacherID
                     AND "AcademicYear" = p_AcademicYear
                     AND "SchoolID" = p_SchoolID
                     AND "IsClassTeacher" = 1
                     AND "ClassID" != p_ClassID;

                     IF v_ConflictCount > 0 THEN
                        RETURN QUERY SELECT 'ERROR'::VARCHAR, 'Teacher is already assigned as class teacher for another class.'::VARCHAR;
                        RETURN;
                     END IF;
                END IF;

                IF p_Action = 'INSERT' THEN
                    INSERT INTO "TeacherClassAssignment" (
                        "SchoolID", "TeacherID", "ClassID", "SectionID", "SubjectID", "AcademicYear",
                        "StartDate", "EndDate", "IsClassTeacher", "AssignmentOrder", "Remarks",
                        "CreatedBy", "CreatedAt", "IsActive", "IsDeleted"
                    )
                    VALUES (
                        p_SchoolID, p_TeacherID, p_ClassID, p_SectionID, p_SubjectID, p_AcademicYear,
                        p_StartDate, p_EndDate, CASE WHEN p_IsClassTeacher THEN 1 ELSE 0 END, p_AssignmentOrder, p_Remarks,
                        p_CreatedBy, CURRENT_TIMESTAMP, 1, false
                    );
                    RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Assignment created successfully'::VARCHAR;
                
                ELSIF p_Action = 'UPDATE' THEN
                    UPDATE "TeacherClassAssignment"
                    SET "TeacherID" = p_TeacherID,
                        "ClassID" = p_ClassID,
                        "SectionID" = p_SectionID,
                        "SubjectID" = p_SubjectID,
                        "AcademicYear" = p_AcademicYear,
                        "StartDate" = p_StartDate,
                        "EndDate" = p_EndDate,
                        "IsClassTeacher" = CASE WHEN p_IsClassTeacher THEN 1 ELSE 0 END,
                        "AssignmentOrder" = p_AssignmentOrder,
                        "Remarks" = p_Remarks,
                        "UpdatedBy" = p_CreatedBy,
                        "UpdatedAt" = CURRENT_TIMESTAMP
                    WHERE "AssignmentID" = p_AssignmentID;
                    RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Assignment updated successfully'::VARCHAR;
                END IF;
            END;
            $$ LANGUAGE plpgsql;
            """,
            
            """
            -- Proc_TeacherClassAssignment_Report
            CREATE OR REPLACE FUNCTION "Proc_TeacherClassAssignment_Report"(
                p_SchoolID INT,
                p_AcademicYear VARCHAR DEFAULT NULL,
                p_TeacherName VARCHAR DEFAULT NULL,
                p_ClassName VARCHAR DEFAULT NULL,
                p_SubjectName VARCHAR DEFAULT NULL,
                p_Search VARCHAR DEFAULT NULL,
                p_Page INT DEFAULT 1,
                p_PageSize INT DEFAULT 25,
                p_OrderBy VARCHAR DEFAULT 'TeacherName',
                p_OrderDir VARCHAR DEFAULT 'ASC'
            )
            RETURNS TABLE (
                "AssignmentID" INT,
                "TeacherName" VARCHAR,
                "ClassName" VARCHAR,
                "SectionName" VARCHAR,
                "SubjectName" VARCHAR,
                "AcademicYear" VARCHAR,
                "StartDate" DATE,
                "EndDate" DATE,
                "IsClassTeacher" INT,
                "TotalCount" BIGINT,
                "ActiveCount" BIGINT
            ) AS $$
            DECLARE
                v_Offset INT;
            BEGIN
                v_Offset := (p_Page - 1) * p_PageSize;
                
                RETURN QUERY
                WITH FilteredData AS (
                    SELECT 
                        tca."AssignmentID",
                        e."EmployeeName" AS "TeacherName",
                        c."ClassName",
                        s."SectionName",
                        sub."SubjectName",
                        tca."AcademicYear",
                        tca."StartDate",
                        tca."EndDate",
                        tca."IsClassTeacher"
                    FROM "TeacherClassAssignment" tca
                    JOIN "EmployeeMaster" e ON tca."TeacherID" = e."EmployeeID"
                    JOIN "ClassMaster" c ON tca."ClassID" = c."ClassID"
                    LEFT JOIN "SectionMaster" s ON tca."SectionID" = s."SectionID"
                    JOIN "SubjectMaster" sub ON tca."SubjectID" = sub."SubjectID"
                    WHERE tca."SchoolID" = p_SchoolID
                    AND tca."IsDeleted" = false
                    AND (p_AcademicYear IS NULL OR tca."AcademicYear" = p_AcademicYear)
                    AND (p_TeacherName IS NULL OR e."EmployeeName" ILIKE '%' || p_TeacherName || '%')
                    AND (p_ClassName IS NULL OR c."ClassName" ILIKE '%' || p_ClassName || '%')
                    AND (p_SubjectName IS NULL OR sub."SubjectName" ILIKE '%' || p_SubjectName || '%')
                    AND (p_Search IS NULL OR 
                            e."EmployeeName" ILIKE '%' || p_Search || '%' OR 
                            c."ClassName" ILIKE '%' || p_Search || '%' OR
                            sub."SubjectName" ILIKE '%' || p_Search || '%'
                        )
                ),
                Counts AS (
                    SELECT 
                        COUNT(*) AS "TotalCount",
                        COUNT(*) FILTER (WHERE "EndDate" IS NULL OR "EndDate" >= CURRENT_DATE) AS "ActiveCount"
                    FROM FilteredData
                )
                SELECT 
                    fd."AssignmentID",
                    fd."TeacherName",
                    fd."ClassName",
                    fd."SectionName",
                    fd."SubjectName",
                    fd."AcademicYear",
                    fd."StartDate",
                    fd."EndDate",
                    fd."IsClassTeacher",
                    ct."TotalCount",
                    ct."ActiveCount"
                FROM FilteredData fd
                CROSS JOIN Counts ct
                ORDER BY
                    CASE WHEN p_OrderBy = 'TeacherName' AND p_OrderDir = 'ASC' THEN fd."TeacherName" END ASC,
                    CASE WHEN p_OrderBy = 'TeacherName' AND p_OrderDir = 'DESC' THEN fd."TeacherName" END DESC,
                    CASE WHEN p_OrderBy = 'ClassName' AND p_OrderDir = 'ASC' THEN fd."ClassName" END ASC,
                    CASE WHEN p_OrderBy = 'ClassName' AND p_OrderDir = 'DESC' THEN fd."ClassName" END DESC
                LIMIT p_PageSize OFFSET v_Offset;
            END;
            $$ LANGUAGE plpgsql;
            """
        ]

        with connection.cursor() as cursor:
            for proc in procedures:
                try:
                    cursor.execute(proc)
                    self.stdout.write(self.style.SUCCESS(f'Successfully executed procedure chunk starting with: {proc.strip()[:50]}...'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error executing procedure chunk: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Successfully set up all Teachers & Staff PostgreSQL functions'))
