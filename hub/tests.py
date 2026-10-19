import json
from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.management import call_command
from django.utils import timezone
from .models import *
class HubTests(TestCase):
    @classmethod
    def setUpTestData(cls):call_command('seed_demo')
    def login(self,name='ana'):self.client.login(username=name,password='DemoQA!2026')
    def attempt(self):
        self.login();a=Assessment.objects.first();self.client.post(f'/exam/{a.pk}/start/');return Attempt.objects.latest('pk')
    def test_auth_and_roles(self):
        self.assertEqual(self.client.get('/').status_code,302);self.login();self.assertEqual(self.client.get('/p/users/').status_code,403);self.assertEqual(self.client.get('/report.xlsx').status_code,403)
    def test_all_admin_screens(self):
        self.login('admin')
        from .views import NAV
        for slug,_,_ in NAV:self.assertEqual(self.client.get('/p/'+slug+'/').status_code,200,slug)
        r=Resource.objects.first();self.assertEqual(self.client.get(f'/resource/{r.pk}/').status_code,200)
    def test_autosave_grade_and_ownership(self):
        a=self.attempt();answers={str(q.pk):q.correct for q in a.assessment.questions.all()}
        self.assertEqual(self.client.get(f'/attempt/{a.pk}/').status_code,200)
        self.assertEqual(self.client.post(f'/attempt/{a.pk}/save/',json.dumps(answers),content_type='application/json').status_code,200)
        self.client.post(f'/attempt/{a.pk}/finish/');a.refresh_from_db();self.assertEqual(a.score,100)
        self.assertEqual(self.client.get(f'/results/{a.pk}/').status_code,200)
        self.login('diego');self.assertEqual(self.client.get(f'/attempt/{a.pk}/').status_code,404)
    def test_expired_rejects_answers(self):
        a=self.attempt();a.deadline=timezone.now()-timedelta(seconds=1);a.save()
        self.assertEqual(self.client.post(f'/attempt/{a.pk}/save/','{}',content_type='application/json').status_code,409)
        a.refresh_from_db();self.assertTrue(a.finished);self.assertEqual(a.answers,{})
    def test_progress_idempotent(self):
        self.login();l=Lesson.objects.first()
        for _ in range(2):self.client.post(f'/lesson/{l.pk}/complete/')
        self.assertEqual(Progress.objects.count(),1)
    def test_search_and_protected_file(self):
        self.login();self.assertContains(self.client.get('/p/library/?q=batch&area=Mainframe'),'Guía de pruebas batch')
        v=ResourceVersion.objects.exclude(file='').first();self.assertEqual(self.client.get(f'/download/{v.pk}/').status_code,200)
        v.resource.published=False;v.resource.save();self.assertEqual(self.client.get(f'/download/{v.pk}/').status_code,404)
    def test_invalid_answers(self):
        a=self.attempt();self.assertEqual(self.client.post(f'/attempt/{a.pk}/save/','{"999":0}',content_type='application/json').status_code,400)
    def test_excel_and_backup(self):
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        from openpyxl import load_workbook
        self.login('lucia');template=self.client.get('/template/');self.assertEqual(template.status_code,200)
        before=Question.objects.count();upload=SimpleUploadedFile('questions.xlsx',template.content)
        self.assertEqual(self.client.post('/import/',{'file':upload}).status_code,200);self.assertEqual(Question.objects.count(),before+1)
        self.assertEqual(self.client.get('/report.xlsx').status_code,200);self.assertEqual(self.client.post('/backup/').status_code,200)
        wb=load_workbook(BytesIO(template.content));wb.active.append([1,'Broken',None,None,None,9,'No']);out=BytesIO();wb.save(out)
        before=Question.objects.count();self.assertEqual(self.client.post('/import/',{'file':SimpleUploadedFile('bad.xlsx',out.getvalue())}).status_code,400);self.assertEqual(Question.objects.count(),before)
