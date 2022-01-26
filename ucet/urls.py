from django.urls import path

from .views import Login, LoginFailure, LoginComplete, Logout

app_name = "ucet"

urlpatterns = [
    path(
        "login/",
        Login.as_view(),
        name="login"),
    
    path(
        "login/complete/",
        LoginComplete.as_view(),
        name="complete"),
    
    path(
        "login/failure/",
        LoginFailure.as_view(),
        name="failure"),
    
    path(
        "logout/",
        Logout.as_view(),
        name="logout"),
]
