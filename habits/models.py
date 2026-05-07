from django.db import models
from django.contrib.auth.models import User

#class dels habits concrets
class Habit(models.Model):
    name = models.CharField(max_length=100)
    #description = models.TextField(blank=True)
    icon = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name


#class dels habits de cada user
class UserHabit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE)
    goal = models.IntegerField(default=1)
    #created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.habit.name}"


#class del progres de cada habit de cada user
class HabitTracking(models.Model):
    user_habit = models.ForeignKey(UserHabit, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    progress = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user_habit} - {self.progress}"