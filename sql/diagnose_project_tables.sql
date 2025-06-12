-- Check for existing project-related objects
SELECT 'TABLES' as object_type, table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE '%project%' OR table_name LIKE '%task%'

UNION ALL

SELECT 'VIEWS' as object_type, table_name 
FROM information_schema.views 
WHERE table_schema = 'public' 
AND (table_name LIKE '%project%' OR table_name LIKE '%task%')

UNION ALL

SELECT 'TRIGGERS' as object_type, trigger_name 
FROM information_schema.triggers 
WHERE trigger_schema = 'public'
AND (event_object_table LIKE '%project%' OR event_object_table LIKE '%task%')

ORDER BY object_type, table_name;