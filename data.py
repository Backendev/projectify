import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from dotenv import load_dotenv
from g_token import TokenGen
import os
from singleton import Singleton
from data_aux import DataAux
from datetime import datetime

class Data(metaclass=Singleton):


    def __init__(self):
        config = os.environ.get('CONFIG_FIREBASE',os.getenv('CONFIG_FIREBASE'))
        self.cred = credentials.Certificate(config)
        firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()
        self.user_col = self.db.collection(u'users')
        self.projects_col = self.db.collection(u'projects')
        self.reports_col = self.db.collection(u'reports')
        self.da = DataAux()


    def get_project(self,name):
        project = list(self.projects_col.where(u'name', u'==',name).stream())
        l = len(list(project))
        result = None
        if l > 0:
            for doc in project:
                result = doc.to_dict(),doc.id
        return result


    def get_user_id(self,idu):
        doc = self.user_col.document(u''+str(idu)).get()
        res = None
        res = doc.to_dict()
        return res


    def get_user(self,user,passd=None,idu=None):

        docs = []
        if idu != None:
            users = list(self.user_col.where(u'user', u'==',user).stream())
            if users[0].id == idu:
                docs = users
        elif passd != None:
            passd = self.da.cipher_pass(passd)
            docs = list(self.user_col.where(u'user', u'==',user).where(u'pass',u'==',passd).stream())
        else:
            docs = list(self.user_col.where(u'user', u'==',user).stream())
        l = len(list(docs))
        result = None
        if l > 0:
            for doc in docs:
                result = doc.to_dict(),doc.id
        return result
    
    
    def new_user(self,user,passd):
        user_old = self.get_user(user=user)
        result = None
        if user_old != None:
            result = "Usuario "+str(user)+" ya existe"
        else:
            passd = self.da.cipher_pass(passd)
            docs = list(self.user_col.stream())
            ids = int(len(docs))
            new_id = ids +1
            new_user = self.user_col.document(u''+str(new_id))
            res = new_user.set({
                u'user': user,
                u'pass':passd
            })
            result = "Usuario "+str(user)+" creado"
        return result
    

    def new_project(self,start,end,name):
        start_year,start_month,start_day = self.da.split_date(start)
        end_year,end_month,end_day = self.da.split_date(end)
        start_date  = datetime(start_year,start_month,start_day)
        end_date  = datetime(end_year,end_month,end_day)
        list_weeks = self.da.weeks_range(start_date,end_date)
        project_old = self.get_project(name)
        if project_old != None:
            result = "Proyecto "+str(name)+" ya existe!!"
        else:
            projects = list(self.projects_col.stream())
            ids = int(len(projects))
            new_id = ids +1
            new_project = self.projects_col.document(u''+str(new_id))
            new_project.set({
                u'name':name,
                u'start_date':str(start_date),
                u'end_date':str(end_date),
                u'weeks_list':list_weeks
            })
            result = "Proyecto "+str(name)+" creado!!"
        return result

    def new_report(self,user,name,week,porcent):
        project_old = self.get_project(name)
        if project_old == None:
            return "El proyecto no existe"
        else:
            project_id = project_old[1]
            project = project_old[0]
            weeks = list(project['weeks_list'])
            weeks_month =  self.da.week_range_month(datetime.now())
            if not week in weeks_month:
                return "La semena no esta en el rango del mes actual"
            if week in weeks:
                reports = list(self.reports_col.stream())
                ids = int(len(reports))
                new_id = ids +1
                new_report = self.reports_col.document(u''+str(new_id))
                new_report.set({
                    u'user':user,
                    u'project':str(project_id),
                    u'week':str(week),
                    u'porcent':porcent
                })
                return "reporte en semana "+str(week)+" con "+str(porcent)+"% creado!!"
            else:
                return "La semena no esta en el rango de semanas estimadas en el proyecto"
    
    def get_reports(self,name=None):
        results = {}
        projects = list(self.projects_col.stream())
        reports = None
        res_reports = {}
        if name == None:
            reports = list(self.reports_col.stream())
            for doc in reports:
                res_reports[doc.id] = doc.to_dict()
        else:
            user = list(self.user_col.where(u'user', u'==',name).stream())
            user_id = str(user[0].id)
            reports = list(self.reports_col.where(u'user', u'==',user_id).stream())
            for doc in reports:
                res_reports[doc.id] = doc.to_dict()
        users = list(self.user_col.stream())
        res_users = {}
        res_projects = {}
        for doc in users:
            res_users[doc.id] = doc.to_dict()
        for doc in projects:
            res_projects[doc.id] = doc.to_dict()
        for k,v in res_projects.items():
            results[v['name']] = {}
            weeks_range = v['weeks_list']
            results[v['name']]['weeks_range'] = list(weeks_range)
        for k,v in res_reports.items():
            project = res_projects[v['project']]['name']
            user = [res_users[v['user']]][0]['user']
            if not user in results[project]:
                results[project][user] = {}
            results[project][user][v['week']] = v['porcent']
        return results




        





