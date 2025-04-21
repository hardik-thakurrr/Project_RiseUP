from django.db import models
from django.utils import timezone
import uuid

class Login(models.Model):
    username = models.TextField(null=True, blank=True)
    email = models.TextField(null=True, blank=True)
    authToken = models.TextField(null=True, blank=True)
    password = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = "login"

    def __int__(self):
        return self.pk
    
class File(models.Model):
    userId = models.ForeignKey(Login, on_delete=models.CASCADE, related_name='files', db_column="userId")
    filename = models.CharField(max_length=255, blank=True)
    totalPages = models.IntegerField(default=1)
    addedOn = models.DateTimeField(default=timezone.now)
    fileStatus = models.CharField(max_length=45, default="Processing")
    ocrText = models.TextField(null=True, blank=True)
    hasTable = models.BooleanField(default=False) 

    class Meta:
        db_table = "file"
    
    def __str__(self):
        return self.filename
    
class StaticData(models.Model):
    key = models.CharField(max_length=50, null=True, blank=True)
    value = models.CharField(max_length=1000, null=True, blank=True)

    class Meta:
        db_table = "staticdata_table"
        
    def __str__(self):
        return self.key
    
class ResumeInsights(models.Model):
    fileId = models.ForeignKey(File, on_delete=models.CASCADE, related_name='insights', db_column="fileId")
    name = models.CharField(max_length=255, blank=True,null=True)
    email = models.CharField(max_length=255, blank=True,null=True)
    phone = models.CharField(max_length=255, blank=True,null=True)
    skills = models.JSONField(blank=True, null=True)
    experience = models.JSONField(blank=True, null=True)
    education = models.JSONField(blank=True, null=True)
    projects = models.JSONField(blank=True, null=True)
    certifications = models.JSONField(blank=True, null=True)
    domain = models.CharField(max_length=255, blank=True,null=True)
    roles = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = "resume_insights"
    
    def __str__(self):
        return self.filename
    
class InterviewSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    userId = models.ForeignKey(Login, on_delete=models.CASCADE, related_name='interviews', db_column="userId")
    fileId = models.ForeignKey(File, on_delete=models.CASCADE, related_name='interviews', db_column="fileId")
    qnaJson = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    progress = models.CharField(max_length=5, default="0")
    reportStatus = models.CharField(max_length=45, default="Pending")
    score = models.IntegerField(default=0)
    summary = models.TextField(null=True, blank=True)