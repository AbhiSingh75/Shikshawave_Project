from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0085_subscriber_pagination_support'), 
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DROP FUNCTION IF EXISTS fn_subscriber_get_list(integer, integer, character varying, boolean, character varying);
            """,
            reverse_sql="" # Reversing might be complex, leaving empty for now
        )
    ]
