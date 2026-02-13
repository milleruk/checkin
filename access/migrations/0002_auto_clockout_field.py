from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('access', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='accessevent',
            name='auto_clockout',
            field=models.BooleanField(default=False, help_text='True if this event was an automatic clock-out at 23:00 GMT.'),
        ),
    ]
