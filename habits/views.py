from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from .models import Habit, UserHabit, HabitTracking
from datetime import date
from django.db.models import F
from django.contrib import messages

def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()

    return render(request, 'habits/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()

    return render(request, 'habits/login.html', {'form': form})


def home(request):
    return render(request, 'habits/home.html')


@login_required
def dashboard(request):
    
    user = request.user
    today = date.today()

    #obtenir habits actius de l'usuari
    user_habits = UserHabit.objects.filter(user=user).select_related("habit")


    #assegurar un tracking per cada UserHabit
    for uh in user_habits:
        HabitTracking.objects.get_or_create(user_habit=uh, date=today)

    #obtenir trackings d'avui
    habit_trackings = HabitTracking.objects.filter(
        user_habit__user=user,
        date=today
    ).select_related("user_habit", "user_habit__habit")

    #
    for t in habit_trackings:
        goal = t.user_habit.goal if t.user_habit.goal > 0 else 1
        percentage = int((t.progress / goal) * 100)
        if percentage > 100:
            percentage = 100
        t.percentage = percentage

    #habits completats amb data d'avui
    completed = HabitTracking.objects.filter(
        user_habit__user=user,
        date=today,
        progress__gte=F('user_habit__goal')
    ).count()
    return render(request, "habits/dashboard.html", {
        "habit_trackings": habit_trackings,
        "completed": completed,
    })

def logout_view(request):
    return render(request, 'habits/logout.html')

@login_required
def edit_habits(request):
    habits = Habit.objects.all()
    user = request.user


    user_habits = UserHabit.objects.filter(user=user)
    selected_ids = [uh.habit.id for uh in user_habits]

    if request.method == "POST":
        new_habit_name = request.POST.get("new_habit")

        if new_habit_name:
            Habit.objects.create(name=new_habit_name)
            messages.success(request, "Hàbit creat correctament")
            return redirect("edit_habits")
            
        selected = request.POST.getlist("habits")

        #convertir ids a enters
        selected = list(map(int, selected))

        #eliminar si no estan marcats
        for uh in user_habits:
            if uh.habit.id not in selected:
                uh.delete()

        #crear els marcats nous i actualitzar les metes
        for habit_id in selected:
            habit = Habit.objects.get(id=habit_id)

            uh, created = UserHabit.objects.get_or_create(
                user=user,
                habit=habit,
            )

            #llegir el goal associat
            goal_value = request.POST.get(f"goal_{habit_id}", "0")
            try:
                uh.goal = int(goal_value)
            except:
                uh.goal = 0

            uh.save()
            
        #els canvis es desen i retorna al dashboard    
        messages.success(request, "Canvis desats correctament")
        return redirect("dashboard")

    return render(request, "habits/edit_habits.html", {
        "habits": habits,
        "user_habits": user_habits,
        "selected": selected_ids,
    })

def update_habit(request, tracking_id, action):
    tracking = get_object_or_404(HabitTracking, id=tracking_id)

    #si la acció es afegir i no es major que el valor del goal
    if action == "add" and tracking.progress < tracking.user_habit.goal:
        tracking.progress += 1
    #si no, borra progres si el progrés es major que 0
    elif action == "remove" and tracking.progress > 0:
        tracking.progress -= 1
    
    #guarda el tracking
    tracking.save()

    if request.GET.get("from") == "detail":
        return redirect("habit_detail", tracking_id=tracking_id)

    #si no, torna al dashboard
    return redirect("dashboard")


@login_required
def habit_detail(request, tracking_id):
    tracking = get_object_or_404(HabitTracking, id=tracking_id, user_habit__user=request.user)

    user_habit = tracking.user_habit
    habit_name = user_habit.habit.name
    progress = tracking.progress
    goal = tracking.user_habit.goal if tracking.user_habit.goal > 0 else 1 

    percentage = int((progress / goal) * 100)
    if percentage > 100:
        percentage = 100

    history = HabitTracking.objects.filter(
        user_habit=user_habit
    ).order_by('-date')[:7]

    #retorna la pagina de habit_detail
    return render(request, "habits/habit_detail.html", {
        "tracking": tracking,
        "progress": progress,
        "goal": goal,
        "percentage": percentage,
        "habit_name": habit_name,
        "history": history,
    })

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')