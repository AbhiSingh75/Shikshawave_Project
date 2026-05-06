-- Optimize Admission Page Performance
-- Add indexes for faster dropdown queries

-- Index for Geographical_Master (Countries, States, Districts)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Geographical_Master_Type_Parent')
CREATE NONCLUSTERED INDEX IX_Geographical_Master_Type_Parent 
ON Geographical_Master(Geog_Type, Geog_Parent_Id, IsDeleted) 
INCLUDE (Geog_Id, Geog_Name);

-- Index for ClassMaster
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_ClassMaster_School')
CREATE NONCLUSTERED INDEX IX_ClassMaster_School 
ON ClassMaster(SchoolID, IsDeleted) 
INCLUDE (ClassID, ClassName);

-- Index for SectionMaster
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_SectionMaster_Class')
CREATE NONCLUSTERED INDEX IX_SectionMaster_Class 
ON SectionMaster(ClassID) 
INCLUDE (SectionID, SectionName);

-- Index for FeeTypeMaster
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_FeeTypeMaster_School_Class')
CREATE NONCLUSTERED INDEX IX_FeeTypeMaster_School_Class 
ON FeeTypeMaster(SchoolId, ClassId, IsDeleted) 
INCLUDE (FeeTypeId, FeeTypeName, DefaultAmount);

PRINT 'Indexes created successfully for admission page optimization';
