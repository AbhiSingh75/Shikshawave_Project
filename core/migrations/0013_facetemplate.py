# Generated migration for FaceTemplate model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_delete_feepayment_delete_feestructure_delete_payment_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FaceTemplate',
            fields=[
                ('FaceTemplateID', models.AutoField(primary_key=True, serialize=False)),
                ('FaceDescriptor', models.TextField()),
                ('TemplateVersion', models.CharField(default='1.0', max_length=10)),
                ('IsActive', models.BooleanField(default=True)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('UpdatedAt', models.DateTimeField(auto_now=True)),
                ('CreatedBy', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='face_template_created_by', to='core.usermaster')),
                ('UpdatedBy', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='face_template_updated_by', to='core.usermaster')),
                ('UserID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='face_templates', to='core.usermaster')),
            ],
            options={
                'db_table': 'FaceTemplates',
                'managed': False,
            },
        ),
    ]
