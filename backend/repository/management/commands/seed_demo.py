from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from repository.models import Campus,School,Department,Profile
class Command(BaseCommand):
    def handle(self,*args,**kwargs):
        c,_=Campus.objects.get_or_create(name="Main Campus",code="MAIN"); s,_=School.objects.get_or_create(name="School of Computing and Information Technology",code="SCIT"); d,_=Department.objects.get_or_create(school=s,code="CS",defaults={"name":"Computer Science"})
        data=[("student","Student123!","student@aru.ac.tz","STUDENT","STU/001/2026"),("supervisor1","Supervisor123!","supervisor1@aru.ac.tz","SUPERVISOR",""),("supervisor2","Supervisor123!","supervisor2@aru.ac.tz","SUPERVISOR","")]
        for un,pw,email,role,reg in data:
            u,created=User.objects.get_or_create(username=un,defaults={"email":email,"first_name":un.title()})
            if created: u.set_password(pw); u.save()
            Profile.objects.update_or_create(user=u,defaults={"role":role,"registration_number":reg,"campus":c,"school":s,"department":d,"approval_status":"APPROVED"})
        self.stdout.write(self.style.SUCCESS("Demo data ready."))
