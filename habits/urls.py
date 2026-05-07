from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('habit/update/<int:tracking_id>/<str:action>/', views.update_habit, name='update_habit'),
    path('habit/edit/', views.edit_habits, name='edit_habits'),
    #utilitza la id de l'usuari per generar l'habit detail
    path('habit/<int:tracking_id>/', views.habit_detail, name='habit_detail'),
    path('edit-habits/', views.edit_habits, name='edit_habits'),
    
    
]

#configuració per fer servir arxius estàtics
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)