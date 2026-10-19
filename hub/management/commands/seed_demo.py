from django.core.management.base import BaseCommand
from django.contrib.auth.models import User,Group,Permission
from django.core.files.base import ContentFile
from hub.models import *
class Command(BaseCommand):
    help='Carga datos ficticios. Idempotente; nunca usar en producción.'
    def handle(self,*args,**kwargs):
        roles={
            'Participante':[],
            'Editor':['view_resource','add_resource','change_resource','view_resourceversion','add_resourceversion','change_resourceversion','view_learningpath','add_learningpath','change_learningpath','view_lesson','add_lesson','change_lesson'],
            'Evaluador':['view_question','add_question','change_question','view_assessment','add_assessment','change_assessment','view_audit'],
            'Administrador':list(Permission.objects.values_list('codename',flat=True))}
        for name,codes in roles.items():
            group,_=Group.objects.get_or_create(name=name); group.permissions.set(Permission.objects.filter(codename__in=codes))
        for username,first,last,role in [('admin','Carlos','Demo','Administrador'),('ana','Ana','Torres','Participante'),('diego','Diego','Ramos','Editor'),('lucia','Lucía','Vega','Evaluador')]:
            user,created=User.objects.get_or_create(username=username,defaults={'first_name':first,'last_name':last,'is_staff':role!='Participante','is_superuser':username=='admin'})
            if created:user.set_password('DemoQA!2026');user.save()
            user.groups.add(Group.objects.get(name=role))
        resources=[
            ('Guía de pruebas batch y JCL','Mainframe','Documento','Diseña una estrategia de validación batch: revisa condiciones de ejecución, códigos de retorno, datasets de entrada y salida y reconciliación de totales.\nEjercicio: define evidencias para un job que procesa 1.000 registros, rechaza 20 y genera 980 resultados.',''),
            ('Checklist de pruebas de API REST','Distribuido','Documento','Planifica casos positivos y negativos, autenticación, contratos, idempotencia y manejo de errores. Ejercicio: verifica que una solicitud no autorizada no altere el estado del sistema.',''),
            ('Introducción a DB2 para QA','Mainframe','Video','Sesión de referencia: consultas, integridad y comparación de resultados. El recurso enlazado es documentación pública de IBM, no una grabación incluida.','https://www.ibm.com/docs/en/db2-for-zos'),
            ('Automatización de servicios con Python','Distribuido','Video','Guion de práctica: organiza datos, ejecuta solicitudes y compara resultados esperados. El enlace abre documentación de Python; el video debe cargarse en una fase posterior.','https://docs.python.org/3/'),
            ('Documentación de Django','Distribuido','Enlace','Consulta oficial para modelos, autenticación, vistas y pruebas.','https://docs.djangoproject.com/'),
            ('Centro de documentación z/OS','Mainframe','Enlace','Punto de consulta oficial para procesos y herramientas del entorno z/OS.','https://www.ibm.com/docs/en/zos')]
        for title,area,kind,description,url in resources:
            r,_=Resource.objects.get_or_create(title=title,defaults=dict(area=area,kind=kind,description=description,url=url))
            for number,notes in [(1,'Publicación inicial revisada por QA.'),(2,'Incluye escenarios negativos y criterios de evidencia.')]:
                v,created=ResourceVersion.objects.get_or_create(resource=r,number=number,defaults={'notes':notes})
                if created and kind=='Documento':v.file.save(f'guia-{r.pk}-v{number}.txt',ContentFile((title+'\n\n'+description+'\n\n'+notes).encode('utf-8')))
        for area,title in [('Mainframe','Fundamentos QA Mainframe'),('Distribuido','QA de servicios distribuidos')]:
            path,_=LearningPath.objects.get_or_create(title=title,defaults={'area':area,'description':'Aprende con escenarios prácticos y evidencia verificable.'})
            topics=[('Diseñar una estrategia de pruebas','Identifica riesgos, dependencias y criterios de aceptación.\nPráctica: enumera tres fallos que impidan procesar una transacción y define cómo detectarlos.'),('Preparar datos y evidencias','Crea datos sintéticos reproducibles y conserva valores esperados.\nMainframe: concilia conteos y códigos de retorno. Distribuido: valida contrato, estado y efectos persistidos.'),('Validar y comunicar resultados','Compara resultados observados con lo esperado. Documenta pasos, datos, evidencia y severidad.\nPráctica: redacta un defecto que otro profesional pueda reproducir.')]
            for n,(t,b) in enumerate(topics,1):Lesson.objects.get_or_create(path=path,position=n,defaults={'title':t,'body':b})
            assessment,_=Assessment.objects.get_or_create(title=title,defaults={'area':area})
            if not assessment.questions.exists():
                questions=[('¿Qué evidencia demuestra la integridad del procesamiento?',['Conciliación de entradas, salidas y rechazos','Solo una captura del inicio','El nombre del archivo'],0,'La conciliación permite explicar el destino de cada registro.'),('¿Qué debe incluir un defecto reproducible?',['Solo la severidad','Pasos, datos, resultado esperado y observado','Una opinión general'],1,'Los pasos y datos hacen posible reproducir y verificar el defecto.'),('¿Qué objetivo tiene una prueba negativa?',['Evaluar entradas inválidas y manejo de errores','Duplicar los casos exitosos','Omitir validaciones'],0,'Debe comprobarse un rechazo controlado sin efectos indebidos.')]
                for text,options,correct,explanation in questions:Question.objects.create(assessment=assessment,text=text,options=options,correct=correct,explanation=explanation)
        from hub.catalog import CONTENT
        for slug,label,area,title,body in CONTENT:
            Resource.objects.update_or_create(title=title,defaults={'area':area,'kind':slug,'description':body,'published':True})
        path,_=LearningPath.objects.get_or_create(title='Academia CICC: certificación integral',defaults={'area':'Transversal','description':'Desde el ambiente y los componentes hasta la evidencia y los incidentes.'})
        for position,(_,_,_,title,body) in enumerate(CONTENT[:10],1):
            Lesson.objects.update_or_create(path=path,position=position,defaults={'title':title,'body':body})
        self.stdout.write(self.style.SUCCESS('Datos demo disponibles: admin, ana, diego, lucia / DemoQA!2026'))
