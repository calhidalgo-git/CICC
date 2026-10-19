from django.contrib import admin
from .models import Resource,ResourceVersion,LearningPath,Lesson,Assessment,Question,Audit,Progress,Attempt
for model in [Resource,ResourceVersion,LearningPath,Lesson,Assessment,Question,Audit,Progress,Attempt]: admin.site.register(model)

admin.site.site_header='CICC — Centro Integral de Conocimiento de Calidad'
admin.site.site_title='CICC'
admin.site.index_title='Sección de Control de Calidad'
