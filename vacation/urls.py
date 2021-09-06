from django.urls import path

from vacation import views

app_name = "vacation"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("manage", views.VacationManagementView.as_view(), name="manage"),
    path("<int:user_id>", views.VacationListView.as_view(), name="list"),
    path("register", views.VacationCreateView.as_view(), name="register"),
    path("<int:pk>/update", views.VacationUpdateView.as_view(), name="update"),
    path("<int:pk>/delete", views.VacationDeleteView.as_view(), name="delete"),
    path("admin/", views.AdminIndexView.as_view(), name="admin"),
    path(
        "admin/<int:pk>/update",
        views.AdminVacationUpdateView.as_view(),
        name="admin_update",
    ),
    path("admin/users", views.MemberListView.as_view(), name="member_list"),
    path("admin/register/sick", views.SickCreateView.as_view(), name="sick"),
    path(
        "admin/users/vacation",
        views.UserVacationListView.as_view(),
        name="users_vacation",
    ),
    path(
        "admin/user/<int:pk>/update",
        views.UserVacationDayUpdateView.as_view(),
        name="vacation_update",
    ),
    path(
        "admin/<int:pk>/approval", views.VacationApprovalView.as_view(), name="approval"
    ),
]
