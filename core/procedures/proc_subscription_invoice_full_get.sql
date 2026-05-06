-- Function: proc_subscription_invoice_full_get
-- Purpose: Fetches all data required for a subscription invoice in a single JSON call
-- FIX: Updated table name from SubscriptionPlans to subscriptionplan and corrected casing

CREATE OR REPLACE FUNCTION public."proc_subscription_invoice_full_get"(p_subscription_id BIGINT)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'invoice_master', (
            SELECT jsonb_build_object(
                'InvoiceNumber', m."InvoiceNumber",
                'InvoiceDate', m."InvoiceDate",
                'DueDate', m."DueDate",
                'TotalAmount', m."TotalAmount",
                'TaxAmount', m."TaxAmount",
                'DiscountAmount', m."DiscountAmount",
                'FinalAmount', m."FinalAmount",
                'PaymentStatus', m."PaymentStatus",
                'CreatedBy', m."CreatedBy",
                'TemplateUrl', m."TemplateUrl"
            )
            FROM "InvoiceMaster" m
            WHERE m."SubscriptionID" = p_subscription_id
            LIMIT 1
        ),
        'school_details', (
            SELECT jsonb_build_object(
                'SchoolID', s."SchoolID",
                'SchoolCode', s."SchoolCode",
                'SchoolName', s."SchoolName",
                'Address', s."Address",
                'District', COALESCE(dist."Geog_Name", s."District"::TEXT),
                'State', COALESCE(st."Geog_Name", s."State"::TEXT),
                'Country', COALESCE(cnt."Geog_Name", s."Country"::TEXT),
                'Phone', s."Phone",
                'Email', s."Email"
            )
            FROM "SchoolMaster" s
            JOIN "Subscriber" sub ON s."SchoolID" = sub."SchoolId"
            LEFT JOIN "Geographical_Master" dist ON s."District" = dist."Geog_Id" AND dist."Geog_Type" = 'District'
            LEFT JOIN "Geographical_Master" st ON s."State" = st."Geog_Id" AND st."Geog_Type" = 'State'
            LEFT JOIN "Geographical_Master" cnt ON s."Country" = cnt."Geog_Id" AND cnt."Geog_Type" = 'Country'

            WHERE sub."SubscriberID" = p_subscription_id
            LIMIT 1
        ),
        'plan_details', (
            SELECT jsonb_build_object(
                'PlanName', p.planname,
                'SubscriptionNo', sub."SubscriptionNo",
                'DurationMonths', sub."DurationMonths",
                'StartDate', sub."SubscriptionStartDate",
                'EndDate', sub."SubscriptionEndDate"
            )
            FROM "Subscriber" sub
            JOIN subscriptionplan p ON sub."PlanID" = p.planid
            WHERE sub."SubscriberID" = p_subscription_id
            LIMIT 1
        ),
        'invoice_items', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'ItemName', i."ItemName",
                    'Description', i."Description",
                    'Quantity', i."Quantity",
                    'UnitPrice', i."UnitPrice",
                    'TotalPrice', i."TotalPrice"
                )
            )
            FROM "InvoiceItems" i
            WHERE i."InvoiceID" = (SELECT "InvoiceID" FROM "InvoiceMaster" WHERE "SubscriptionID" = p_subscription_id)
        ),
        'payment_transactions', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'PaymentMode', t."PaymentMode",
                    'TransactionRef', t."TransactionRef",
                    'Amount', t."Amount",
                    'PaymentDate', t."PaymentDate",
                    'Status', t."Status"
                )
            )
            FROM "PaymentTransactions" t
            WHERE t."InvoiceID" = (SELECT "InvoiceID" FROM "InvoiceMaster" WHERE "SubscriptionID" = p_subscription_id)
        ),
        'footer_info', (
            SELECT jsonb_build_object(
                'Disclaimer', 'Certified Document — This is an electronically generated tax invoice issued by ShikshaWave Advanced Agentic Systems.',
                'CopyrightNotice', '© ' || EXTRACT(YEAR FROM CURRENT_DATE)::TEXT || ' ' || (SELECT "BrandName" FROM "BrandProfile" LIMIT 1) || '. Strategic Intellectual Property of ShikshaWave Pvt Ltd.',
                'TermsAndConditions', '1. All disputes are subject to the jurisdiction of Noida courts.
2. Goods once sold will not be taken back.
3. Payment to be made via Online Transfer/UPI only.',
                'LegalDeclaration', 'I/We hereby certify that my/our registration certificate under the GST Act is in force on the date on which the sale of the goods specified in this tax invoice is made by me/us and that the transaction of sale covered by this tax invoice has been effected by me/us and it shall be accounted for in the turnover of sales while filing of return and the due tax, if any, payable on the sale has been paid or shall be paid'
            )
        )
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql;
