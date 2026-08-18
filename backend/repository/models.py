from django.contrib.auth.models import User
from django.db import models

class Campus(models.Model):
    name=models.CharField(max_length=120,unique=True); code=models.CharField(max_length=30,unique=True)
    def __str__(self): return self.name
class School(models.Model):
    name=models.CharField(max_length=180,unique=True); code=models.CharField(max_length=30,unique=True)
    def __str__(self): return self.name
class Department(models.Model):
    school=models.ForeignKey(School,on_delete=models.CASCADE,related_name="departments")
    name=models.CharField(max_length=180); code=models.CharField(max_length=30)
    class Meta: constraints=[models.UniqueConstraint(fields=["school","code"],name="unique_department_code_per_school")]
    def __str__(self): return f"{self.code} — {self.name}"
class Profile(models.Model):
    ROLE_CHOICES=[("STUDENT","Student"),("SUPERVISOR","Supervisor"),("LECTURER","Lecturer"),("ADMIN","Administrator")]
    APPROVAL_CHOICES=[("APPROVED","Approved"),("PENDING","Pending"),("REJECTED","Rejected")]
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name="profile")
    role=models.CharField(max_length=20,choices=ROLE_CHOICES,default="STUDENT")
    phone=models.CharField(max_length=30,blank=True); registration_number=models.CharField(max_length=80,blank=True)
    campus=models.ForeignKey(Campus,null=True,blank=True,on_delete=models.SET_NULL,related_name="profiles")
    school=models.ForeignKey(School,null=True,blank=True,on_delete=models.SET_NULL,related_name="profiles")
    department=models.ForeignKey(Department,null=True,blank=True,on_delete=models.SET_NULL,related_name="profiles")
    approval_status=models.CharField(max_length=20,choices=APPROVAL_CHOICES,default="APPROVED")
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.user.get_full_name() or self.user.username} ({self.role})"
class Project(models.Model):
    STATUS_CHOICES=[("DRAFT","Draft"),("SUBMITTED","Submitted"),("APPROVED","Approved"),("CHANGES_REQUESTED","Changes requested"),("REJECTED","Rejected"),("PUBLISHED","Published"),("ARCHIVED","Archived")]
    TYPE_CHOICES=[("INDIVIDUAL","Individual"),("GROUP","Group")]
    title=models.CharField(max_length=255); abstract=models.TextField(); project_type=models.CharField(max_length=20,choices=TYPE_CHOICES,default="INDIVIDUAL")
    student=models.ForeignKey(User,on_delete=models.CASCADE,related_name="projects")
    campus=models.ForeignKey(Campus,on_delete=models.PROTECT,related_name="projects")
    school=models.ForeignKey(School,on_delete=models.PROTECT,related_name="projects")
    department=models.ForeignKey(Department,on_delete=models.PROTECT,related_name="projects")
    course=models.CharField(max_length=160); academic_year=models.CharField(max_length=20); technology=models.CharField(max_length=255,blank=True); topic=models.CharField(max_length=160,blank=True); keywords=models.CharField(max_length=500,blank=True); license=models.CharField(max_length=100,default="CC BY")
    status=models.CharField(max_length=30,choices=STATUS_CHOICES,default="DRAFT")
    supervisor1=models.ForeignKey(User,on_delete=models.PROTECT,related_name="supervised_projects_1"); supervisor2=models.ForeignKey(User,on_delete=models.PROTECT,related_name="supervised_projects_2")
    review_comment=models.TextField(blank=True); created_at=models.DateTimeField(auto_now_add=True); submitted_at=models.DateTimeField(null=True,blank=True); updated_at=models.DateTimeField(auto_now=True)
    def __str__(self): return self.title
class Notification(models.Model):
    TYPE_CHOICES=[("PROJECT_SUBMITTED","Project submitted"),("SUPERVISOR_APPROVAL","Supervisor approval"),("REVIEW_OUTCOME","Review outcome"),("GENERAL","General")]
    recipient=models.ForeignKey(User,on_delete=models.CASCADE,related_name="notifications"); title=models.CharField(max_length=200); message=models.TextField(); notification_type=models.CharField(max_length=30,choices=TYPE_CHOICES,default="GENERAL"); project=models.ForeignKey(Project,null=True,blank=True,on_delete=models.CASCADE,related_name="notifications"); is_read=models.BooleanField(default=False); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=["-created_at"]
class SupervisorApproval(models.Model):
    supervisor=models.OneToOneField(Profile,on_delete=models.CASCADE,related_name="supervisor_approval")
    approved_by=models.ForeignKey(User,null=True,blank=True,on_delete=models.SET_NULL,related_name="supervisor_approvals")
    decision=models.CharField(max_length=20,choices=[("PENDING","Pending"),("APPROVED","Approved"),("REJECTED","Rejected")],default="PENDING")
    comment=models.TextField(blank=True); decided_at=models.DateTimeField(null=True,blank=True)
