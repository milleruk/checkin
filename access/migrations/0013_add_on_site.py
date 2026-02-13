from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("access", "0012_remove_associatedstaff_company_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="accessevent",
            name="on_site",
            field=models.BooleanField(default=True, help_text="True for physical on-site events; False for remote/WFH events."),
        ),
    ]
