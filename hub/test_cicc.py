from django.test import TestCase
from django.core.management import call_command
from .models import Resource, Lesson
from .catalog import MODULES, CONTENT

class CICCTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo')

    def setUp(self):
        self.client.login(username='ana', password='DemoQA!2026')

    def test_modules_and_brand(self):
        for slug in MODULES:
            response=self.client.get('/p/'+slug+'/')
            self.assertContains(response,'CICC — Centro Integral de Conocimiento de Calidad')
            self.assertContains(response,Resource.objects.filter(kind=slug).first().title)
        self.assertContains(self.client.get('/p/components/'),'CICS → COBOL → DATACOM')

    def test_search_body_academy_and_unpublished(self):
        response=self.client.get('/p/search/',{'q':'980'})
        self.assertContains(response,'JCL, COBOL, ROSCOE/TSO y Batch',count=2)
        hidden=Resource.objects.create(title='OCULTO',description='980',area='Mainframe',published=False)
        self.assertNotContains(self.client.get('/p/search/?q=980'),hidden.title)
        self.assertEqual(self.client.get(f'/resource/{hidden.pk}/').status_code,404)

    def test_seed_repeat_and_transversal_validation(self):
        counts=(Resource.objects.count(),Lesson.objects.count())
        call_command('seed_demo')
        self.assertEqual(counts,(Resource.objects.count(),Lesson.objects.count()))
        for r in Resource.objects.filter(area='Transversal'):
            r.full_clean()
        self.assertEqual(len(CONTENT),26)

    def test_global_search_does_not_expose_answers(self):
        response=self.client.get('/p/search/?q=evidencia')
        self.assertNotContains(response,'La conciliación permite explicar el destino de cada registro.')
        self.assertEqual(self.client.get('/p/questions/').status_code,403)
