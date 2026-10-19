from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator,MaxValueValidator
class Resource(models.Model):
    title=models.CharField(max_length=200)
    area=models.CharField(max_length=20,choices=[('Mainframe','Mainframe'),('Distribuido','Distribuido'),('Transversal','Transversal')])
    kind=models.CharField(max_length=20,default='Documento')
    description=models.TextField()
    url=models.URLField(blank=True)
    published=models.BooleanField(default=True)
    @property
    def display_kind(self):
        from .catalog import MODULES
        return MODULES.get(self.kind,self.kind)
    def __str__(self): return self.title
class ResourceVersion(models.Model):
    resource=models.ForeignKey(Resource,on_delete=models.CASCADE,related_name='versions')
    number=models.PositiveIntegerField()
    notes=models.TextField()
    file=models.FileField(upload_to='resources/%Y/%m',blank=True)
    created=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['resource','number'],name='unique_version')]
class LearningPath(models.Model):
    title=models.CharField(max_length=200)
    area=models.CharField(max_length=20)
    description=models.TextField()
class Lesson(models.Model):
    path=models.ForeignKey(LearningPath,on_delete=models.CASCADE,related_name='lessons')
    title=models.CharField(max_length=200)
    body=models.TextField()
    position=models.PositiveIntegerField()
    class Meta: ordering=['position']
class Progress(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    lesson=models.ForeignKey(Lesson,on_delete=models.CASCADE)
    class Meta: constraints=[models.UniqueConstraint(fields=['user','lesson'],name='unique_progress')]
class Assessment(models.Model):
    title=models.CharField(max_length=200)
    area=models.CharField(max_length=20)
    minutes=models.PositiveIntegerField(default=20,validators=[MinValueValidator(1),MaxValueValidator(240)])
    pass_score=models.PositiveIntegerField(default=70,validators=[MaxValueValidator(100)])
class Question(models.Model):
    assessment=models.ForeignKey(Assessment,on_delete=models.CASCADE,related_name='questions')
    text=models.TextField()
    options=models.JSONField(default=list)
    correct=models.PositiveSmallIntegerField()
    explanation=models.TextField()
    def clean(self):
        if not isinstance(self.options,list) or len(self.options)<2 or any(not isinstance(o,str) or not o.strip() for o in self.options):
            raise ValidationError({'options':'Ingresa una lista JSON de al menos dos opciones de texto.'})
        if self.correct is None or not 0<=self.correct<len(self.options):
            raise ValidationError({'correct':'El índice debe corresponder a una opción, comenzando en cero.'})
class Attempt(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    assessment=models.ForeignKey(Assessment,on_delete=models.PROTECT)
    started=models.DateTimeField(auto_now_add=True)
    deadline=models.DateTimeField()
    answers=models.JSONField(default=dict)
    finished=models.BooleanField(default=False)
    score=models.FloatField(default=0)
    updated=models.DateTimeField(auto_now=True)
class Audit(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,on_delete=models.SET_NULL)
    action=models.CharField(max_length=200)
    created=models.DateTimeField(auto_now_add=True)
