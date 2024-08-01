from django.urls import path
from .views import RegisterUser, DeleteUser, UsersList, ChangeUser, UserData, ChangeStatusAdmin

urlpatterns = [
    path('', UsersList.as_view(), name='users-list'),
    path('<int:user_id>/', UserData.as_view(), name='user_data'),
    path('changestatusadmin/<int:userId>/', ChangeStatusAdmin.as_view(), name='change-status-admin'),
    path('register/', RegisterUser.as_view(), name='register'),
    path('delete/<int:userId>/', DeleteUser.as_view(), name='delete'),
    path('change/<int:userId>/', ChangeUser.as_view(), name='delete'),
]