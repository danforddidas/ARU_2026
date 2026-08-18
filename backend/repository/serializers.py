from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from .models import Campus,School,Department,Profile,Project,Notification,SupervisorApproval
class CampusSerializer(serializers.ModelSerializer):
    class Meta: model=Campus; fields=["id","name","code"]
class SchoolSerializer(serializers.ModelSerializer):
    class Meta: model=School; fields=["id","name","code"]
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta: model=Department; fields=["id","name","code","school"]
class UserSerializer(serializers.ModelSerializer):
    full_name=serializers.SerializerMethodField(); role=serializers.SerializerMethodField(); approval_status=serializers.SerializerMethodField()
    class Meta: model=User; fields=["id","username","email","full_name","role","approval_status"]
    def get_full_name(self,obj): return obj.get_full_name() or obj.username
    def get_role(self,obj): return getattr(getattr(obj,"profile",None),"role","STUDENT")
    def get_approval_status(self,obj): return getattr(getattr(obj,"profile",None),"approval_status","APPROVED")
class RegisterSerializer(serializers.Serializer):
    username=serializers.CharField(max_length=80); email=serializers.EmailField(); password=serializers.CharField(write_only=True,min_length=8); first_name=serializers.CharField(max_length=80); last_name=serializers.CharField(max_length=80); phone=serializers.CharField(max_length=30,required=False,allow_blank=True); registration_number=serializers.CharField(max_length=80,required=False,allow_blank=True); role=serializers.ChoiceField(choices=["STUDENT","SUPERVISOR"]); campus=serializers.PrimaryKeyRelatedField(queryset=Campus.objects.all(),required=False,allow_null=True); school=serializers.PrimaryKeyRelatedField(queryset=School.objects.all(),required=False,allow_null=True); department=serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(),required=False,allow_null=True)
    def validate(self,a):
        if User.objects.filter(username=a["username"]).exists(): raise serializers.ValidationError({"username":"Username already exists."})
        if User.objects.filter(email=a["email"]).exists(): raise serializers.ValidationError({"email":"Email already exists."})
        if a["role"]=="STUDENT" and not all([a.get("campus"),a.get("school"),a.get("department")]): raise serializers.ValidationError("Student must select campus, school and department.")
        return a
    @transaction.atomic
    def create(self,a):
        role=a.pop("role"); campus=a.pop("campus",None); school=a.pop("school",None); department=a.pop("department",None); phone=a.pop("phone",""); reg=a.pop("registration_number",""); password=a.pop("password")
        u=User.objects.create_user(password=password,**a); approval="PENDING" if role=="SUPERVISOR" else "APPROVED"
        Profile.objects.create(user=u,role=role,phone=phone,registration_number=reg,campus=campus,school=school,department=department,approval_status=approval)
        if role=="SUPERVISOR": SupervisorApproval.objects.create(supervisor=u.profile)
        return u
class ProjectSerializer(serializers.ModelSerializer):
    student_name=serializers.SerializerMethodField(); supervisor1_name=serializers.SerializerMethodField(); supervisor2_name=serializers.SerializerMethodField(); status_display=serializers.CharField(source="get_status_display",read_only=True)
    class Meta:
        model=Project; fields=["id","title","abstract","project_type","student","student_name","campus","school","department","course","academic_year","technology","topic","keywords","license","status","status_display","supervisor1","supervisor1_name","supervisor2","supervisor2_name","review_comment","created_at","submitted_at","updated_at"]; read_only_fields=["student","status","review_comment","submitted_at"]
    def get_student_name(self,o): return o.student.get_full_name() or o.student.username
    def get_supervisor1_name(self,o): return o.supervisor1.get_full_name() or o.supervisor1.username
    def get_supervisor2_name(self,o): return o.supervisor2.get_full_name() or o.supervisor2.username
    def validate(self,a):
        s1,s2=a.get("supervisor1"),a.get("supervisor2")
        if not s1 or not s2 or s1==s2: raise serializers.ValidationError("Choose exactly two different supervisors.")
        for s in [s1,s2]:
            p=getattr(s,"profile",None)
            if not p or p.role!="SUPERVISOR" or p.approval_status!="APPROVED": raise serializers.ValidationError("Both supervisors must be approved.")
        return a
class NotificationSerializer(serializers.ModelSerializer):
    class Meta: model=Notification; fields=["id","title","message","notification_type","project","is_read","created_at"]
class SupervisorApprovalSerializer(serializers.ModelSerializer):
    supervisor_name=serializers.SerializerMethodField(); email=serializers.EmailField(source="supervisor.user.email",read_only=True); school_name=serializers.CharField(source="supervisor.school.name",read_only=True); department_name=serializers.CharField(source="supervisor.department.name",read_only=True)
    class Meta: model=SupervisorApproval; fields=["id","supervisor","supervisor_name","email","school_name","department_name","decision","comment","decided_at"]
    def get_supervisor_name(self,o): return o.supervisor.user.get_full_name() or o.supervisor.user.username
