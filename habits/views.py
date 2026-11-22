from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from .models import Habit, UserHabit, HabitTracking
from datetime import date, timedelta
from django.db.models import F, Q
from django.contrib import messages
from django.views.decorators.cache import never_cache

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

def contacte(request):
    return render(request, 'habits/contacte.html')

#NeverCache per quan es deslogeja, no poder tornar enrere

@never_cache
@login_required
def dashboard(request):
    
    user = request.user
    today = date.today()

    #obtenir habits actius de l'usuari
    user_habits = UserHabit.objects.filter(user=user).select_related("habit")


    #assegurar un tracking per cada UserHabit amb data d'avui
    for uh in user_habits:
        HabitTracking.objects.get_or_create(user_habit=uh, date=today)

    #obtenir trackings d'avui
    habit_trackings = HabitTracking.objects.filter(
        user_habit__user=user,
        date=today
    ).select_related("user_habit", "user_habit__habit")


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


@never_cache
@login_required
def estadistiques(request):

    user = request.user
    today = date.today()

    #obtenir habits actius de l'usuari
    user_habits = UserHabit.objects.filter(
        user=user
    ).select_related("habit")

    #obtenir trackings d'avui
    habit_trackings = HabitTracking.objects.filter(
        user_habit__user=user,
        date=today
    ).select_related("user_habit", "user_habit__habit")

    #si el progress es major o igual a la goal, conta 1 més com a completat
    completed = habit_trackings.filter(
        progress__gte=F('user_habit__goal')
    ).count()

    #conta el total d'habits
    total = habit_trackings.count()

    #percentatge dividint el total per mostrar a l'estadística
    if total > 0:
        percentage = int((completed / total) * 100)
    else:
        percentage = 0


    #registres dels últims 7 dies
    last_trackings = HabitTracking.objects.filter(
        user_habit__user=user,
        date__range=[
            today - timedelta(days=6),
            today
        ]
    ).select_related(
        "user_habit",
        "user_habit__habit"
    )


    #crear els 7 dies de l'historial
    history = []

    for i in range(6, -1, -1):

        day = today - timedelta(days=i)

        day_trackings = [
            tracking for tracking in last_trackings
            if tracking.date == day
        ]

        if day_trackings:

            total_day = len(day_trackings)

            completed_day = sum(
                1 for tracking in day_trackings
                if tracking.progress >= tracking.user_habit.goal
            )

            percentage_day = int(
                (completed_day / total_day) * 100
            )

            history.append({
                "date": day,
                "has_data": True,
                "completed": completed_day,
                "total": total_day,
                "percentage": percentage_day,
            })

        else:

            history.append({
                "date": day,
                "has_data": False,
                "completed": 0,
                "total": 0,
                "percentage": 0,
            })


    return render(request, 'habits/estadistiques.html', {
        "user_habits": user_habits,
        "habit_trackings": habit_trackings,
        "completed": completed,
        "total": total,
        "percentage": percentage,
        "history": history,
    })

@never_cache
@login_required
def edit_habits(request):
    user = request.user

    #obtenir habits generals i els creats pel propi usuari
    habits = Habit.objects.filter(
        Q(user__isnull=True) | Q(user=user)
    )

    user_habits = UserHabit.objects.filter(user=user)
    selected_ids = [uh.habit.id for uh in user_habits]

    if request.method == "POST":
        new_habit_name = request.POST.get("new_habit")
        new_habit_icon = request.POST.get("new_habit_icon")
        new_habit_color = request.POST.get("new_habit_color")

        if new_habit_name:

            icon_path = f"habits/icons/custom/{new_habit_icon}_{new_habit_color}.png"

            Habit.objects.create(
                name=new_habit_name,
                icon=icon_path,
                user=user
            )

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
            habit = get_object_or_404(
                Habit.objects.filter(
                    Q(user__isnull=True) | Q(user=user)
                ),
                id=habit_id
            )

            uh, created = UserHabit.objects.get_or_create(
                user=user,
                habit=habit,
            )

            #llegir el goal associat
            goal_value = request.POST.get(f"goal_{habit_id}", "1")

            #llegir la unitat associada
            unit_value = request.POST.get(f"unit_{habit_id}", "unitats")

            try:
                goal = int(goal_value)

                if goal < 1:
                    goal = 1

                uh.goal = goal

            except (ValueError, TypeError):
                uh.goal = 1

            if unit_value.strip():
                uh.unit = unit_value.strip()
            else:
                uh.unit = "unitats"

            uh.save()
            
        #els canvis es desen i retorna al dashboard    
        messages.success(request, "Canvis desats correctament")
        return redirect("dashboard")

    return render(request, "habits/edit_habits.html", {
        "habits": habits,
        "user_habits": user_habits,
        "selected": selected_ids,
    })
    
@login_required
def update_habit(request, tracking_id, action):
    tracking = get_object_or_404(
        HabitTracking,
        id=tracking_id,
        user_habit__user=request.user
    )

    #si la acció es afegir i no es major que el valor del goal
    if action == "add" and tracking.progress < tracking.user_habit.goal:
        tracking.progress += 1

    #si es remove resta progres si el progrés es major que 0
    elif action == "remove" and tracking.progress > 0:
        tracking.progress -= 1

    #guarda el tracking
    tracking.save()

    if request.GET.get("from") == "detail":
        return redirect("habit_detail", tracking_id=tracking_id)

    #si no, torna al dashboard
    return redirect("dashboard")

@never_cache
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

    #dies en què l'hàbit s'ha completat
    completed_dates = set(
        HabitTracking.objects.filter(
            user_habit=user_habit,
            progress__gte=F('user_habit__goal')
        ).values_list('date', flat=True)
    )

    #calcular la ratxa actual
    today = date.today()

    if today in completed_dates:
        current_day = today
    else:
        current_day = today - timedelta(days=1)

    streak = 0

    while current_day in completed_dates:
        streak += 1
        current_day -= timedelta(days=1)

    #calcular la millor ratxa
    best_streak = 0
    temporary_streak = 0
    previous_day = None

    for completed_day in sorted(completed_dates):

        if previous_day and completed_day == previous_day + timedelta(days=1):
            temporary_streak += 1
        else:
            temporary_streak = 1

        if temporary_streak > best_streak:
            best_streak = temporary_streak

        previous_day = completed_day

    #retorna la pagina de habit_detail
    return render(request, "habits/habit_detail.html", {
        "tracking": tracking,
        "progress": progress,
        "goal": goal,
        "percentage": percentage,
        "habit_name": habit_name,
        "history": history,
        "streak": streak,
        "best_streak": best_streak,
    })

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')