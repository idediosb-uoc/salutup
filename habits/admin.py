from django.contrib import admin
from .models import Habit, UserHabit, HabitTracking

admin.site.register(Habit)
admin.site.register(UserHabit)
admin.site.register(HabitTracking)
# Register your models here.
