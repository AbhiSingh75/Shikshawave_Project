-- Verify Timetable Tables and Procedures Exist

-- Check if tables exist
SELECT 'PeriodMaster' AS TableName, 
       CASE WHEN OBJECT_ID('PeriodMaster', 'U') IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END AS Status
UNION ALL
SELECT 'TimetableMaster', 
       CASE WHEN OBJECT_ID('TimetableMaster', 'U') IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END
UNION ALL
SELECT 'TimetableSlot', 
       CASE WHEN OBJECT_ID('TimetableSlot', 'U') IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END;

-- Check if procedures exist
SELECT 'Proc_PeriodMaster_Manage' AS ProcedureName,
       CASE WHEN OBJECT_ID('Proc_PeriodMaster_Manage', 'P') IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END AS Status
UNION ALL
SELECT 'Proc_Timetable_Manage',
       CASE WHEN OBJECT_ID('Proc_Timetable_Manage', 'P') IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END
UNION ALL
SELECT 'Proc_TimetableSlot_Manage',
       CASE WHEN OBJECT_ID('Proc_TimetableSlot_Manage', 'P') IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END
UNION ALL
SELECT 'Proc_Timetable_GetView',
       CASE WHEN OBJECT_ID('Proc_Timetable_GetView', 'P') IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END;

-- If any are missing, run the INSTALL_TIMETABLE_COMPLETE.sql script
