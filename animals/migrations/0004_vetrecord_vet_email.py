from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("animals", "0003_alter_animal_unique_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="vetrecord",
            name="vet_email",
            field=models.EmailField(blank=True, max_length=254, verbose_name="Email сотрудника"),
        ),
    ]
