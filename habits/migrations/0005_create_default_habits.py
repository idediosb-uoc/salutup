from django.db import migrations


def create_default_habits(apps, schema_editor):
    Habit = apps.get_model("habits", "Habit")

    default_habits = [
        {
            "name": "Hidratació",
            "icon": "habits/icons/drop.png",
        },
        {
            "name": "Alimentació",
            "icon": "habits/icons/cutlery.png",
        },
        {
            "name": "Exercici",
            "icon": "habits/icons/dumbbell.png",
        },
        {
            "name": "Descans",
            "icon": "habits/icons/sleep-mode.png",
        },
    ]

    for habit in default_habits:
        Habit.objects.get_or_create(
            name=habit["name"],
            user=None,
            defaults={
                "icon": habit["icon"],
            }
        )


class Migration(migrations.Migration):

    dependencies = [
        ("habits", "0004_userhabit_unit"),
    ]

    operations = [
        migrations.RunPython(create_default_habits),
    ]