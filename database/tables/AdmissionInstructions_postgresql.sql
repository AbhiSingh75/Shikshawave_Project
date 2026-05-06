-- PostgreSQL compatible table for Admission Instructions
-- Run this if the table doesn't exist already

CREATE TABLE IF NOT EXISTS "AdmissionInstructions" (
    "InstructionID" SERIAL PRIMARY KEY,
    "SchoolID" INT NOT NULL,
    "InstructionTitle" VARCHAR(200) NOT NULL,
    "InstructionText" VARCHAR(1000) NOT NULL,
    "DisplayOrder" INT DEFAULT 0,
    "IsActive" BOOLEAN DEFAULT TRUE,
    "CreatedBy" INT,
    "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "ModifiedBy" INT,
    "ModifiedAt" TIMESTAMP,
    "IsDeleted" BOOLEAN DEFAULT FALSE,
    FOREIGN KEY ("SchoolID") REFERENCES "SchoolMaster"("SchoolID")
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_admission_instructions_school 
ON "AdmissionInstructions"("SchoolID", "IsDeleted");
