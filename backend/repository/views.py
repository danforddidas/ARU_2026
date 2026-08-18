from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from rest_framework import status,viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action,api_view,permission_classes
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from .models import Campus,School,Department,Profile,Project,Notification,SupervisorApproval
from .serializers import CampusSerializer,SchoolSerializer,DepartmentSerializer,RegisterSerializer,UserSerializer,ProjectSerializer,NotificationSerializer,SupervisorApprovalSerializer
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    s=RegisterSerializer(data=request.data); s.is_valid(raise_exception=True); u=s.save(); t,_=Token.objects.get_or_create(user=u)
    msg="Registration successful." if u.profile.role=="STUDENT" else "Supervisor registration submitted. Wait for lecturer/admin approval."
    return Response({"message":msg,"token":t.key,"user":UserSerializer(u).data},status=201)
@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    u=authenticate(username=request.data.get("username"),password=request.data.get("password"))
    if not u: return Response({"detail":"Invalid username or password."},status=400)
    if getattr(getattr(u,"profile",None),"role","")=="SUPERVISOR" and u.profile.approval_status!="APPROVED": return Response({"detail":"Supervisor account is awaiting approval."},status=403)
    t,_=Token.objects.get_or_create(user=u); return Response({"token":t.key,"user":UserSerializer(u).data})
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request): return Response(UserSerializer(request.user).data)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def approved_supervisors(request):
    ps=Profile.objects.filter(role="SUPERVISOR",approval_status="APPROVED").select_related("user","school","department")
    return Response([{"id":p.user_id,"name":p.user.get_full_name() or p.user.username,"email":p.user.email,"school":p.school.name if p.school else "","department":p.department.name if p.department else ""} for p in ps])
class CampusViewSet(viewsets.ReadOnlyModelViewSet): queryset=Campus.objects.all().order_by("name"); serializer_class=CampusSerializer; permission_classes=[AllowAny]
class SchoolViewSet(viewsets.ReadOnlyModelViewSet): queryset=School.objects.all().order_by("name"); serializer_class=SchoolSerializer; permission_classes=[AllowAny]
class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class=DepartmentSerializer; permission_classes=[AllowAny]
    def get_queryset(self):
        q=Department.objects.all().order_by("name"); school=self.request.query_params.get("school"); return q.filter(school_id=school) if school else q
class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class=ProjectSerializer
    def get_queryset(self):
        u=self.request.user; qs=Project.objects.select_related("student","supervisor1","supervisor2","campus","school","department")
        role=getattr(getattr(u,"profile",None),"role","")
        if u.is_staff or role in ["ADMIN","LECTURER"]: return qs
        if role=="SUPERVISOR": return qs.filter(Q(supervisor1=u)|Q(supervisor2=u)).distinct()
        return qs.filter(student=u)
    def perform_create(self,serializer): serializer.save(student=self.request.user)
    @action(detail=True,methods=["post"])
    def submit(self,request,pk=None):
        p=self.get_object()
        if p.student!=request.user: return Response({"detail":"Only the owner can submit."},status=403)
        p.status="SUBMITTED"; p.submitted_at=timezone.now(); p.save(update_fields=["status","submitted_at","updated_at"])
        for s in [p.supervisor1,p.supervisor2]: Notification.objects.create(recipient=s,title="New project submitted",message=f"{p.student.get_full_name() or p.student.username} submitted '{p.title}'. You are assigned as one of two supervisors.",notification_type="PROJECT_SUBMITTED",project=p)
        return Response(ProjectSerializer(p,context={"request":request}).data)
    @action(detail=True,methods=["post"])
    def review(self,request,pk=None):
        p=self.get_object(); role=getattr(getattr(request.user,"profile",None),"role","")
        if not (request.user.is_staff or role in ["ADMIN","LECTURER","SUPERVISOR"]): return Response({"detail":"Not allowed."},status=403)
        if role=="SUPERVISOR" and request.user not in [p.supervisor1,p.supervisor2]: return Response({"detail":"Not assigned."},status=403)
        decision=request.data.get("decision")
        if decision not in ["APPROVED","CHANGES_REQUESTED","REJECTED","PUBLISHED"]: return Response({"detail":"Invalid decision."},status=400)
        p.status=decision; p.review_comment=request.data.get("feedback",""); p.save(update_fields=["status","review_comment","updated_at"])
        Notification.objects.create(recipient=p.student,title="Project review updated",message=f"{p.title}: {p.get_status_display()}. {p.review_comment}".strip(),notification_type="REVIEW_OUTCOME",project=p)
        return Response(ProjectSerializer(p,context={"request":request}).data)
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class=NotificationSerializer
    def get_queryset(self): return Notification.objects.filter(recipient=self.request.user).select_related("project")
    @action(detail=True,methods=["post"])
    def mark_read(self,request,pk=None):
        n=self.get_object(); n.is_read=True; n.save(update_fields=["is_read"]); return Response({"success":True})
    @action(detail=False,methods=["get"])
    def summary(self,request):
        unread=self.get_queryset().filter(is_read=False).count(); role=getattr(getattr(request.user,"profile",None),"role","")
        if role=="SUPERVISOR":
            ps=Project.objects.filter(Q(supervisor1=request.user)|Q(supervisor2=request.user)).distinct()
            return Response({"unread_notifications":unread,"supervised_projects":ps.count(),"students_supervised":ps.values("student").distinct().count()})
        return Response({"unread_notifications":unread})
class SupervisorApprovalViewSet(viewsets.ModelViewSet):
    serializer_class=SupervisorApprovalSerializer; http_method_names=["get","post","head","options"]
    def get_queryset(self):
        role=getattr(getattr(self.request.user,"profile",None),"role","")
        return SupervisorApproval.objects.select_related("supervisor__user","supervisor__school","supervisor__department").order_by("-id") if self.request.user.is_staff or role in ["ADMIN","LECTURER"] else SupervisorApproval.objects.none()
    @action(detail=True,methods=["post"])
    def decide(self,request,pk=None):
        a=self.get_object(); d=request.data.get("decision")
        if d not in ["APPROVED","REJECTED"]: return Response({"detail":"Decision must be APPROVED or REJECTED."},status=400)
        a.decision=d; a.comment=request.data.get("comment",""); a.approved_by=request.user; a.decided_at=timezone.now(); a.save()
        a.supervisor.approval_status=d; a.supervisor.save(update_fields=["approval_status"])
        Notification.objects.create(recipient=a.supervisor.user,title="Supervisor account decision",message=f"Your supervisor registration has been {d.lower()}. {a.comment}".strip(),notification_type="SUPERVISOR_APPROVAL")
        return Response(SupervisorApprovalSerializer(a).data)
