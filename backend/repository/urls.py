from django.urls import include,path
from rest_framework.routers import DefaultRouter
from .views import register,login,me,approved_supervisors,CampusViewSet,SchoolViewSet,DepartmentViewSet,ProjectViewSet,NotificationViewSet,SupervisorApprovalViewSet
router=DefaultRouter(); router.register("campuses",CampusViewSet,basename="campus"); router.register("schools",SchoolViewSet,basename="school"); router.register("departments",DepartmentViewSet,basename="department"); router.register("projects",ProjectViewSet,basename="project"); router.register("notifications",NotificationViewSet,basename="notification"); router.register("supervisor-approvals",SupervisorApprovalViewSet,basename="supervisor-approval")
urlpatterns=[path("auth/register/",register),path("auth/login/",login),path("auth/me/",me),path("users/approved-supervisors/",approved_supervisors),path("",include(router.urls))]
