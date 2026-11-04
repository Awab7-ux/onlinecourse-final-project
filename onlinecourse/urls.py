from django.urls import path

from . import views

app_name = "onlinecourse"

urlpatterns = [
    path("", views.course_list, name="course_list"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("course/<int:course_id>/", views.course_details, name="course_details"),
    path("course/<int:course_id>/enroll/", views.enroll, name="enroll"),
    path("<int:course_id>/submit/", views.submit, name="submit"),
    path(
        "course/<int:course_id>/submission/<int:submission_id>/result/",
        views.show_exam_result,
        name="show_exam_result",
    ),
]
