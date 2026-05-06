from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_feepayment_feestructure_paymentreceipt_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE TABLE "Payment" (
                "PaymentID" SERIAL PRIMARY KEY,
                "StudentID" INT NOT NULL,
                "SchoolID" INT NOT NULL,
                "ReceiptNumber" VARCHAR(50) UNIQUE NOT NULL,
                "TotalAmount" DECIMAL(10,2) NOT NULL,
                "PaidAmount" DECIMAL(10,2) NOT NULL,
                "PaymentMode" VARCHAR(50) NOT NULL,
                "TransactionRef" VARCHAR(100) NULL,
                "PaymentStatus" VARCHAR(20) DEFAULT 'Completed',
                "PaymentDate" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                "FeeBreakdown" TEXT NULL,
                "Remarks" VARCHAR(500) NULL,
                "CreatedBy" INT NULL,
                "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                "UpdatedBy" INT NULL,
                "UpdatedAt" TIMESTAMP NULL,
                "IsDeleted" BOOLEAN DEFAULT FALSE,
                
                FOREIGN KEY ("StudentID") REFERENCES "Student"("StudentID"),
                FOREIGN KEY ("SchoolID") REFERENCES "SchoolMaster"("SchoolID"),
                FOREIGN KEY ("CreatedBy") REFERENCES "UserMaster"("UserID"),
                FOREIGN KEY ("UpdatedBy") REFERENCES "UserMaster"("UserID")
            );
            
            CREATE INDEX "IX_Payment_StudentID" ON "Payment"("StudentID");
            CREATE INDEX "IX_Payment_SchoolID" ON "Payment"("SchoolID");
            CREATE INDEX "IX_Payment_PaymentDate" ON "Payment"("PaymentDate");
            CREATE INDEX "IX_Payment_ReceiptNumber" ON "Payment"("ReceiptNumber");
            """,
            reverse_sql='DROP TABLE "Payment";'
        ),
    ]