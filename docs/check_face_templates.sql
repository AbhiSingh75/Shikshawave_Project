-- Check Face Templates for User
-- Replace 'your_email@example.com' with the actual user email/username

-- 1. Check if user exists
SELECT 
    UserID,
    UserCode,
    UserName,
    Email,
    IsActive,
    CASE WHEN UserPhoto IS NOT NULL THEN 'Yes' ELSE 'No' END as HasPhoto,
    CASE WHEN UserPhoto IS NOT NULL THEN LEN(UserPhoto) ELSE 0 END as PhotoSize
FROM UserMaster 
WHERE (UserCode = 'your_email@example.com' OR Email = 'your_email@example.com') 
  AND ISNULL(IsDeleted, 0) = 0;

-- 2. Check face templates for the user
SELECT 
    ft.FaceTemplateID,
    ft.UserID,
    u.UserName,
    u.Email,
    ft.IsActive,
    ft.CreatedAt,
    ft.UpdatedAt,
    CASE WHEN ft.FaceDescriptor IS NOT NULL THEN 'Yes' ELSE 'No' END as HasDescriptor
FROM FaceTemplates ft
INNER JOIN UserMaster u ON ft.UserID = u.UserID
WHERE (u.UserCode = 'your_email@example.com' OR u.Email = 'your_email@example.com')
ORDER BY ft.CreatedAt DESC;

-- 3. Check face authentication settings
SELECT 
    SettingKey,
    SettingValue,
    Description,
    IsActive
FROM FaceAuthSettings
WHERE IsActive = 1;

-- 4. Check recent face authentication logs
SELECT TOP 10
    fal.LogID,
    u.UserName,
    u.Email,
    fal.Similarity,
    fal.IsSuccessful,
    fal.AttemptTime,
    fal.IPAddress
FROM FaceAuthLogs fal
INNER JOIN UserMaster u ON fal.UserID = u.UserID
WHERE (u.UserCode = 'your_email@example.com' OR u.Email = 'your_email@example.com')
ORDER BY fal.AttemptTime DESC;

-- 5. Check if FaceTemplates table exists and has data
SELECT 
    COUNT(*) as TotalTemplates,
    COUNT(CASE WHEN IsActive = 1 THEN 1 END) as ActiveTemplates,
    COUNT(DISTINCT UserID) as UsersWithTemplates
FROM FaceTemplates;

-- Instructions:
-- 1. Replace 'your_email@example.com' with the actual user email/username
-- 2. Run each query separately in SQL Server Management Studio or similar tool
-- 3. Check the results:
--    - Query 1: Should return user details
--    - Query 2: Should return face templates (if any exist)
--    - Query 3: Should return face auth settings
--    - Query 4: Should return recent authentication attempts
--    - Query 5: Should return overall template statistics