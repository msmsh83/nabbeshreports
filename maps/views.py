# Create your views here.
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.template import Context, loader
from django.http import HttpResponse
from django.shortcuts import render_to_response
from legacy.models import Users, AuthUser, SkillsSkill
from django.utils import simplejson
from django.template import Template, Context
from django.template.loader import render_to_string
from django.template import RequestContext
from django.contrib.auth.decorators import permission_required
import datetime
import dateutil.parser
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.db import connection
from django.db import connections
from django.contrib.auth.decorators import login_required,user_passes_test
import sys
import httplib2
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run
from apiclient.errors import HttpError
from oauth2client.client import AccessTokenRefreshError
import cv2
import urllib
import itertools
import json


# Declare constants and set configuration values

# The file with the OAuth 2.0 Client details for authentication and authorization.
CLIENT_SECRETS = 'client_secrets.json'

# A helpful message to display if the CLIENT_SECRETS file is missing.
MISSING_CLIENT_SECRETS_MESSAGE = '%s is missing' % CLIENT_SECRETS

# The Flow object to be used if we need to authenticate.
FLOW = flow_from_clientsecrets(CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/analytics.readonly',
    message=MISSING_CLIENT_SECRETS_MESSAGE)

# A file to store the access token
TOKEN_FILE_NAME = 'analytics.dat'

def prepare_credentials():
  # Retrieve existing credendials
  storage = Storage(TOKEN_FILE_NAME)
  credentials = storage.get()

  # If existing credentials are invalid and Run Auth flow
  # the run method will store any new credentials
  if credentials is None or credentials.invalid:
    credentials = run(FLOW, storage) #run Auth Flow and store credentials

  return credentials
  
def initialize_service():
  # 1. Create an http object
  http = httplib2.Http()

  # 2. Authorize the http object
  # In this tutorial we first try to retrieve stored credentials. If
  # none are found then run the Auth Flow. This is handled by the
  # prepare_credentials() function defined earlier in the tutorial
  credentials = prepare_credentials()
  http = credentials.authorize(http)  # authorize the http object

  # 3. Build the Analytics Service Object with the authorized http object
  return build('analytics', 'v3', http=http)
  
 


@login_required(login_url='/accounts/login/')
def home(request):    
    t = loader.get_template('index.html')   
    return render_to_response('index.html', context_instance=RequestContext(request))


def customQuery(sql, db):
    ##print sql
    if db==0:
        result=customQueryOffline(sql)
        #print result
        return result
    elif db==1:
        result=customQueryLive(sql)
        #print result
        return result
    elif db==2: 
        result=customQueryOld(sql)
        #print result
        return result    
    elif db==3:
        result=customQuerySendy(sql)
        return result    
    
    


def customQueryOffline(sql):
    cursor = connections['offline'].cursor()    
    cursor.execute(sql,[])
    #transaction.commit_unless_managed(using='offline')
    
    result_list = [] 
    for row in cursor.fetchall(): 
        result_list.append(row) 
    return result_list 

def customQueryLive(sql): 
    cursor = connections['live'].cursor()
    cursor.execute(sql,[])
    #transaction.commit_unless_managed(using='live')
    result_list = [] 
    for row in cursor.fetchall(): 
        result_list.append(row) 
    return result_list 

def customQueryOld(sql): 
    cursor = connections['old'].cursor()
    cursor.execute(sql,[])
    #transaction.commit_unless_managed(using='live')
    result_list = [] 
    for row in cursor.fetchall(): 
        result_list.append(row) 
    return result_list 


def customQuerySendy(sql): 
    
    cursor = connections['sendy'].cursor()
    cursor.execute(sql,[])
    #transaction.commit_unless_managed(using='live')
    result_list = [] 
    for row in cursor.fetchall(): 
        result_list.append(row) 
    return result_list 
    
       
@login_required(login_url='/accounts/login/')       
def freelancerdemography_report(request):
    
    t = loader.get_template('./reports/freelancerdemography_report.html')
    c = Context({
        'freelancerdemography_report': freelancerdemography_report,
    })
    return render_to_response('./reports/freelancerdemography_report.html', context_instance=RequestContext(request))

    
    
@csrf_exempt
def freelancerdemography_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)
        grouper = objs['grouper']
        sql = ("select "+grouper+", count(id) as usercount from users where "+grouper+" is not null and "+grouper+" <>''  group by "+grouper+" order by usercount desc")
 
        results = customQuery(sql,0)

        c = Context({'countries': results})
   
        return HttpResponse(render_to_string('freelancersdemography.json', c, context_instance=RequestContext(request)), mimetype='application/json')
        
        
        
        
        
@login_required(login_url='/accounts/login/')
def freelancersgender_report(request):
    
    t = loader.get_template('./reports/freelancersgender_report.html')
    c = Context({
        'freelancersgender_report': freelancersgender_report,
    })
    #return HttpResponse(t.render(c))
    return render_to_response('./reports/freelancersgender_report.html', context_instance=RequestContext(request))
    
            
@csrf_exempt
def freelancersgender_getdata(request):
    if request.method == 'POST':
        #objs = simplejson.loads(request.raw_post_data)
        
        detect("https://s3.amazonaws.com/fideloper.com/faces_orig.jpg")
        
        sql = "select usercount, case gender when 0 then 'Male' when 1 then 'Female' end from \
         (select count(*) as usercount, gender from users where gender < 2 group by gender) total;"
        results = customQuery(sql,0)
        print results
 
        c = Context({'genders': results})
   
        return HttpResponse(render_to_string('freelancersgender.json', c, context_instance=RequestContext(request)), mimetype='application/json')
        
        
        
@login_required(login_url='/accounts/login/')
def freelancerseducation_report(request):
    
    t = loader.get_template('./reports/freelancerseducation_report.html')
    c = Context({
        'freelancerseducation_report': freelancerseducation_report,
    })
    return render_to_response('./reports/freelancerseducation_report.html', context_instance=RequestContext(request))
            
@csrf_exempt
def freelancerseducation_getdata(request):
    if request.method == 'POST':
        #objs = simplejson.loads(request.raw_post_data)

        sql = "select  case degree when 6 then 'Bachelor of Science' when 7 then 'High School' when 5 then 'Bachelor of Arts' when 4 then 'Executive MBA' when 3 then 'MBA' when 2 then 'Masters' when 1 then 'PHD' end as education, usercount from (select count(distinct u.id ) as usercount, edu.degree from education edu inner join users u on edu.id_user=u.id group by edu.degree) total"
        
        print sql
        results = customQuery(sql,0)
        print results
 
        c = Context({'educations': results})
   
        return HttpResponse(render_to_string('freelancerseducation.json', c, context_instance=RequestContext(request)), mimetype='application/json')
        

@login_required(login_url='/accounts/login/')
def freelancersages_report(request):
    
    t = loader.get_template('./reports/freelancersages_report.html')
    c = Context({
        'freelancersages_report': freelancersgender_report,
    })
    #return HttpResponse(t.render(c))
    return render_to_response('./reports/freelancersages_report.html', context_instance=RequestContext(request))

@csrf_exempt            
def freelancersages_getdata(request):
    if request.method == 'POST':
        #objs = simplejson.loads(request.raw_post_data)

        sql = "select  sum(ucount) as usercounts,case when ageu <18 then '1) Under 18' when ageu >= 18 and ageu<=24 then '2) 18 to 24' when ageu >= 25 and ageu<=34 then '3) 25 to 34' when ageu >= 35 then '4) Over 35' END as age_range from (select count(total.id) as ucount, 2013 - total.yobn as ageu from (select t1.id, t1.yob :: integer yobn from(select id, substring(dob,length(dob)-3, length(dob)) as yob from users where dob<>'') t1 where t1.yob ~E'^\\\d+$') total group by ageu order by ageu) total group by age_range order by age_range;"
        results = customQuery(sql,0)

        print sql
        c = Context({'ages': results})
        return HttpResponse(render_to_string('freelancersages.json', c, context_instance=RequestContext(request)), mimetype='application/json')        
        
        
 
@login_required(login_url='/accounts/login/')	
def dashboard(request):
    
    t = loader.get_template('./reports/dashboard.html')
    return render_to_response('./reports/dashboard.html', context_instance=RequestContext(request))
    


@csrf_exempt 
def datefieldtostring(datefieldname, segment):
    day = " Trim(' ' from to_char(date_part('day' , "+datefieldname+"),'09'))  "    
    week = " Trim(' ' from to_char(date_part('week' , "+datefieldname+" + interval '1 DAY'),'09'))  "
    month = " Trim(' ' from to_char(date_part('month' , "+datefieldname+"),'09'))  "
    year = " date_part('year' , "+datefieldname+") "  

    
    if segment== "Day":
        return year+ "||'-'||"+month+"||'-'||"+ day
    elif segment=="Week":
        return year+"||'-'||"+week
    elif segment=="Month":   
        return year+ "||'-'||"+month
    else:
        return year
     
    
    

   
@csrf_exempt 
def dashboard_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)
        #print objs
        
        t1 = objs['fromdate'] + ' 00:00:00+00'
        t2 = objs['todate']  + ' 23:59:59+00'
        
        grouppertext= objs['limit']
 
        print grouppertext
               
        header_sql = ("select msgdate,COALESCE(message_count,0) as message_count,COALESCE(nmessage_count,0) as nmessage_count,COALESCE(allusers_count,0) as allusers_count,COALESCE(freelancer_count,0) as freelancer_count,COALESCE(employers_count,0) as employers_count,COALESCE(realemployers_count,0) as realemployers_count ,COALESCE(job_count,0) as job_count, COALESCE(proposal_count,0) as proposal_count, COALESCE(paidproposal_count,0) as paidproposal_count, COALESCE(application_count,0) as application_count,COALESCE(invitation_count,0) as invitation_count , COALESCE(invoice_count,0) as invoice_count,COALESCE(invoicepaid_count,0) as invoicepaid_count,round(COALESCE(invperjobavg,0),2) as invperjobavg, round(COALESCE(appperjobavg::numeric,0),2) as appperjobavg  from ")
        
        workflow_messages_sql = ("(select count(distinct id) as message_count,"+datefieldtostring("timestamp", grouppertext) + " as msgdate from contracts_message where timestamp>='"+t1+"' and timestamp<='"+t2+"' group by msgdate) contractsmessages left outer join ")
        
        allusers_sql = ("(select count(distinct u.id) as allusers_count, "+datefieldtostring("date_joined", grouppertext) + " as datejoined from users u inner join auth_user au on au.id=u.django_user_id where date_joined>='"+t1+"' and date_joined<='"+t2+"' group by datejoined) allusers on contractsmessages.msgdate=allusers.datejoined left outer join")
        
        freelancers_sql = ("(select count(distinct u.id) as freelancer_count, "+datefieldtostring("date_joined", grouppertext) + " as datejoined from users u inner join auth_user au on au.id=u.django_user_id where u.is_freelancer=true and date_joined>='"+t1+"' and date_joined<='"+t2+"' group by datejoined) freelancers on contractsmessages.msgdate=freelancers.datejoined left outer join")
        
        employers_sql = ("(select count(distinct u.id) as employers_count, "+datefieldtostring("date_joined", grouppertext) + " as datejoined from users u inner join auth_user au on au.id=u.django_user_id where u.is_employer=true and date_joined>='"+t1+"' and date_joined<='"+t2+"' group by datejoined) employers on freelancers.datejoined=employers.datejoined left outer join")
        
        realemployers_sql = ("(select count(distinct u.id) as realemployers_count, "+datefieldtostring("date_joined", grouppertext) + " as datejoined from users u inner join auth_user au on au.id=u.django_user_id inner join contracts_job cj on cj.employer_id=u.id where  date_joined>='"+t1+"' and date_joined<='"+t2+"' group by datejoined) realemployers on contractsmessages.msgdate=realemployers.datejoined left outer join")
        
        jobs_sql =("(select count(id) as job_count,  "+datefieldtostring("created_at", grouppertext) + " as createdat from contracts_job  where created_at>='"+t1+"' and created_at<='"+t2+"' group by createdat) jobs on jobs.createdat=contractsmessages.msgdate  left outer join")
        
        contractsmessages_sql = ("(select count(distinct id) as nmessage_count, "+datefieldtostring("sent_at", grouppertext) + " as sentat from messages_message where sent_at>='"+t1+"' and sent_at<='"+t2+"' group by sentat) messages on messages.sentat=contractsmessages.msgdate   left outer join")
        
        porposals_sql  = ("(select "+datefieldtostring("timestamp", grouppertext) + " as proposalsent,count(*) as proposal_count from contracts_proposal cp inner join contracts_message cm on cp.message_ptr_id=cm.id where timestamp>='"+t1+"' and timestamp<='"+t2+"'  group by proposalsent) proposals on proposals.proposalsent=contractsmessages.msgdate left outer join ")
                
        proposalspaid_sql = ("(select "+datefieldtostring("timestamp", grouppertext) + " as proposalpaid,sum(case when cp.status=4 then 1 else 0 end) as paidproposal_count from contracts_proposal cp inner join contracts_message cm on cp.message_ptr_id=cm.id where timestamp>='"+t1+"' and timestamp<='"+t2+"'  group by proposalpaid) paidproposals on paidproposals.proposalpaid=contractsmessages.msgdate left outer join ")  
                     
        
        application_sql = ("(select count(distinct id) as application_count,"+datefieldtostring("timestamp", grouppertext) + " as appliedat from contracts_application   where timestamp>='"+t1+"' and timestamp<='"+t2+"' group by appliedat) applications on applications.appliedat=contractsmessages.msgdate left outer join ")
                
        invited_sql = ("(select count(*) as invitation_count, "+datefieldtostring("cj.created_at", grouppertext) + " as invited_at  from contracts_job_invited cji inner join contracts_job cj on cj.id=cji.job_id where cj.created_at>='"+t1+"' and cj.created_at<='"+t2+"' group by invited_at) invitations on invitations.invited_at=contractsmessages.msgdate left outer join")
        
        invoicesent_sql = ("(select count(distinct ci.message_ptr_id) as invoice_count,"+datefieldtostring("timestamp", grouppertext) + " as invoicesent from contracts_invoice ci inner join contracts_message cm on ci.message_ptr_id=cm.id where cm.timestamp>='"+t1+"' and cm.timestamp<='"+t2+"' group by invoicesent) invoicessent on invoicessent.invoicesent=contractsmessages.msgdate left outer join ")
        
        invoicepaid_sql = ("(select count(distinct ci.message_ptr_id) as invoicepaid_count,"+datefieldtostring("cm.timestamp", grouppertext) + " as invoicepaid from contracts_invoice ci inner join contracts_message cm on ci.message_ptr_id=cm.id where cm.timestamp>='"+t1+"' and cm.timestamp<='"+t2+"' and ci.status=4 group by invoicepaid) invoicespaid on invoicespaid.invoicepaid=contractsmessages.msgdate left outer join ")
        
        invperjob_sql = ("(select avg(inv.jobinv) as invperjobavg, "+datefieldtostring("cj.created_at", grouppertext) + " as invsentat from contracts_job cj inner join (select count(cji.id) as jobinv,cji.job_id from contracts_job_invited cji  group by cji.job_id) inv on inv.job_id=cj.id group by invsentat) invitationsperjob on invitationsperjob.invsentat=contractsmessages.msgdate left outer join ")
        
        appperjob_sql = ("(select count(ca.id)::float/count(distinct ca.job_id)::float as appperjobavg,"+datefieldtostring("ca.timestamp", grouppertext) + " as appliedat  from contracts_application ca  group by appliedat) applicationperjob on applicationperjob.appliedat=contractsmessages.msgdate ")
        
        sql = (header_sql + workflow_messages_sql + allusers_sql + freelancers_sql + employers_sql + realemployers_sql + jobs_sql + contractsmessages_sql + porposals_sql + proposalspaid_sql + application_sql +invited_sql+ invoicesent_sql + invoicepaid_sql +invperjob_sql +appperjob_sql+  "  order by msgdate")
        
        
        
        
        results = customQuery(sql,0)                                     
        c = Context({'statistics': results})   
        return HttpResponse(render_to_string('dashboard.json', c, context_instance=RequestContext(request)), mimetype='application/json')  
    
@csrf_exempt 
def dashboard_getdata1(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)
        #print objs
        
        t1 = objs['fromdate'] + ' 00:00:00+00'
        t2 = objs['todate']  + ' 23:59:59+00'
        
        print t1
        print t2

        grouppertext= objs['limit']
        #grouppertext = "7"
        if grouppertext=="Month":
            grouper="7"
        else:
            grouper="10"
        
        header_sql = ("select msgdate,COALESCE(message_count,0) as message_count,COALESCE(nmessage_count,0) as nmessage_count,COALESCE(allusers_count,0) as allusers_count,COALESCE(freelancer_count,0) as freelancer_count,COALESCE(employers_count,0) as employers_count,COALESCE(realemployers_count,0) as realemployers_count ,COALESCE(job_count,0) as job_count, COALESCE(proposal_count,0) as proposal_count, COALESCE(paidproposal_count,0) as paidproposal_count, COALESCE(application_count,0) as application_count,COALESCE(invitation_count,0) as invitation_count , COALESCE(invoice_count,0) as invoice_count,COALESCE(invoicepaid_count,0) as invoicepaid_count,round(COALESCE(invperjobavg,0),2) as invperjobavg, round(COALESCE(appperjobavg::numeric,0),2) as appperjobavg  from ")
        
        workflow_messages_sql = ("(select count(distinct id) as message_count,substring(to_char(timestamp,'YYYY-MM-DD HH24:MI:SS'),1,"+grouper+") as msgdate from contracts_message where timestamp>='"+t1+"' and timestamp<='"+t2+"' group by msgdate) contractsmessages left outer join ")
        
        allusers_sql = ("(select count(distinct u.id) as allusers_count, substring(to_char(date_joined,'YYYY-MM-DD HH24:MI:SS'),1,"+grouper+") as datejoined from users u inner join auth_user au on au.id=u.django_user_id where date_joined>='"+t1+"' and date_joined<='"+t2+"' group by datejoined) allusers on contractsmessages.msgdate=allusers.datejoined left outer join")
        
        freelancers_sql = ("(select count(distinct u.id) as freelancer_count, substring(to_char(date_joined,'YYYY-MM-DD HH24:MI:SS'),1,"+grouper+") as datejoined from users u inner join auth_user au on au.id=u.django_user_id where u.is_freelancer=true and date_joined>='"+t1+"' and date_joined<='"+t2+"' group by datejoined) freelancers on contractsmessages.msgdate=freelancers.datejoined left outer join")
        
        employers_sql = ("(select count(distinct u.id) as employers_count, substring(to_char(date_joined,'YYYY-MM-DD HH24:MI:SS'),1,"+grouper+") as datejoined from users u inner join auth_user au on au.id=u.django_user_id where u.is_employer=true and date_joined>='"+t1+"' and date_joined<='"+t2+"' group by datejoined) employers on freelancers.datejoined=employers.datejoined left outer join")
        
        realemployers_sql = ("(select count(distinct u.id) as realemployers_count, substring(to_char(date_joined,'YYYY-MM-DD HH24:MI:SS'),1,"+grouper+") as datejoined from users u inner join auth_user au on au.id=u.django_user_id inner join contracts_job cj on cj.employer_id=u.id where  date_joined>='"+t1+"' and date_joined<='"+t2+"' group by datejoined) realemployers on contractsmessages.msgdate=realemployers.datejoined left outer join")
        
        jobs_sql =("(select count(id) as job_count, substring(to_char(created_at,'YYYY-MM-DD HH24:MI:SS'),1,"+grouper+") as createdat from contracts_job  where created_at>='"+t1+"' and created_at<='"+t2+"' group by createdat) jobs on jobs.createdat=contractsmessages.msgdate  left outer join")
        
        contractsmessages_sql = ("(select count(distinct id) as nmessage_count, substring(to_char(sent_at,'YYYY-MM-DD HH24:MI:SS'),1,"+grouper+") as sentat from messages_message where sent_at>='"+t1+"' and sent_at<='"+t2+"' group by sentat) messages on messages.sentat=contractsmessages.msgdate   left outer join")
        
        porposals_sql  = ("(select substring(to_char(timestamp,'YYYY-MM-DD HH24:MI:SS'),1,"+grouper+") as proposalsent,count(*) as proposal_count from contracts_proposal cp inner join contracts_message cm on cp.message_ptr_id=cm.id where timestamp>='"+t1+"' and timestamp<='"+t2+"'  group by proposalsent) proposals on proposals.proposalsent=contractsmessages.msgdate left outer join ")
                
        proposalspaid_sql = ("(select substring(to_char(timestamp,'YYYY-MM-DD HH24:MI:SS'),1,"+grouper+") as proposalpaid,sum(case when cp.status=4 then 1 else 0 end) as paidproposal_count from contracts_proposal cp inner join contracts_message cm on cp.message_ptr_id=cm.id where timestamp>='"+t1+"' and timestamp<='"+t2+"'  group by proposalpaid) paidproposals on paidproposals.proposalpaid=contractsmessages.msgdate left outer join ")  
                     
        
        application_sql = ("(select count(distinct id) as application_count,substring(to_char(timestamp,'YYYY-MM-DD HH24:MI:SS'),1,"+grouper+") as appliedat from contracts_application   where timestamp>='"+t1+"' and timestamp<='"+t2+"' group by appliedat) applications on applications.appliedat=contractsmessages.msgdate left outer join ")
                
        invited_sql = ("(select count(*) as invitation_count, substring(to_char(cj.created_at,'YYYY-MM-DD HH24:MI:SS'),1,"+grouper+") as invited_at  from contracts_job_invited cji inner join contracts_job cj on cj.id=cji.job_id where cj.created_at>='"+t1+"' and cj.created_at<='"+t2+"' group by invited_at) invitations on invitations.invited_at=contractsmessages.msgdate left outer join")
        
        invoicesent_sql = ("(select count(distinct ci.message_ptr_id) as invoice_count,substring(to_char(cm.timestamp,'YYYY-MM-DD HH24:MI:SS'),1,"+grouper+") as invoicesent from contracts_invoice ci inner join contracts_message cm on ci.message_ptr_id=cm.id where cm.timestamp>='"+t1+"' and cm.timestamp<='"+t2+"' group by invoicesent) invoicessent on invoicessent.invoicesent=contractsmessages.msgdate left outer join ")
        
        invoicepaid_sql = ("(select count(distinct ci.message_ptr_id) as invoicepaid_count,substring(to_char(cm.timestamp,'YYYY-MM-DD HH24:MI:SS'),1,"+grouper+") as invoicepaid from contracts_invoice ci inner join contracts_message cm on ci.message_ptr_id=cm.id where cm.timestamp>='"+t1+"' and cm.timestamp<='"+t2+"' and ci.status=4 group by invoicepaid) invoicespaid on invoicespaid.invoicepaid=contractsmessages.msgdate left outer join ")
        
        invperjob_sql = ("(select avg(inv.jobinv) as invperjobavg, substring(to_char(cj.created_at,'YYYY-MM-DD HH24:MI:SS'),1,"+grouper+") as invsentat from contracts_job cj inner join (select count(cji.id) as jobinv,cji.job_id from contracts_job_invited cji  group by cji.job_id) inv on inv.job_id=cj.id group by invsentat) invitationsperjob on invitationsperjob.invsentat=contractsmessages.msgdate left outer join ")
        
        appperjob_sql = ("(select count(ca.id)::float/count(distinct ca.job_id)::float as appperjobavg,substring(to_char(ca.timestamp,'YYYY-MM-DD HH24:MI:SS'),1,"+grouper+") as appliedat  from contracts_application ca  group by appliedat) applicationperjob on applicationperjob.appliedat=contractsmessages.msgdate ")
        
        sql = (header_sql + workflow_messages_sql + allusers_sql + freelancers_sql + employers_sql + realemployers_sql + jobs_sql + contractsmessages_sql + porposals_sql + proposalspaid_sql + application_sql +invited_sql+ invoicesent_sql + invoicepaid_sql +invperjob_sql +appperjob_sql+  "  order by msgdate")
        
        print datefieldtostring("created_at", "Day")
        results = customQuery(sql,0)                                     
        c = Context({'statistics': results})   
        return HttpResponse(render_to_string('dashboard.json', c, context_instance=RequestContext(request)), mimetype='application/json') 
        
        
@login_required(login_url='/accounts/login/')
def jobs_employers_statistics(request):
    
    t = loader.get_template('./reports/jobs_employers_statistics.html')
    c = Context({
        'jobs_employers_statistics': dashboard,
    })
    return render_to_response('./reports/jobs_employers_statistics.html', context_instance=RequestContext(request))
        
@csrf_exempt 
def jobs_employers_statistics_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)
        #print objs
        
        t1 = objs['fromdate']  + ' 00:00:00+00'
        t2 = objs['todate'] + ' 23:59:59+00'
        

	period = objs['period']
        grouppertext= objs['limit']
        #grouppertext = "Month"
        if grouppertext=="Month":
            grouper="7"
        else:
            grouper="10"
        
        header_sql = ("select datejoined,max(jobs_per_employer),min(jobs_per_employer), round(avg(jobs_per_employer),3), round(median(jobs_per_employer),3)")
        
        from_sql = ("from (select count(cj.id) as jobs_per_employer, u.id,substring(to_char(au.date_joined,'YYYY-MM-DD HH24:MI:SS'),1,"+grouper+") as datejoined from contracts_job cj inner join users u on u.id=cj.employer_id inner join auth_user au on u.django_user_id=au.id where au.date_joined>='"+t1+"' and au.date_joined<='"+t2+"'  and cj.created_at<=(date_joined + INTERVAL '"+period+" Day') group by u.id,au.date_joined order by jobs_per_employer desc) total group by datejoined order by datejoined;")
        sql = (header_sql + from_sql)
        

        results = customQuery(sql,0)

        #print results
 
        c = Context({'statistics': results})
   
        return HttpResponse(render_to_string('jobs_employers_statistics.json', c, context_instance=RequestContext(request)), mimetype='application/json') 
        
@login_required(login_url='/accounts/login/')
def jobs_applications_statistics(request):
    if request.method == 'GET':
    	#objs = simplejson.loads(request.raw_post_data)
    	#print objs
        t = loader.get_template('./reports/jobs_applications_statistics.html')
        #param =  objs['param']
        #c = Context({'jobs_applications_statistics': dashboard, 'param': param})
        
#        return HttpResponse(t.render(c) )
        #return HttpResponse(render_to_string('./reports/jobs_applications_statistics.html', c, context_instance=RequestContext(request)), mimetype='application/html') 
        return render_to_response('./reports/jobs_applications_statistics.html', context_instance=RequestContext(request))
        
        
@csrf_exempt 
def jobs_applications_statistics_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)
        #print objs
        
        t1 = objs['fromdate']  + ' 00:00:00+00'
        t2 = objs['todate'] + ' 23:59:59+00'
        
        keywords = objs['searchkeywords']
        
        contkeywords = objs['contsearchkeywords']
        
        skillkeywords = objs['skillsearchkeywords']
        searchsql = ""
        if keywords <> "":
            searchsql = "and (lower(substring(cj.title,1,40)) like '%%" +keywords.lower() + "%%' or lower(substring(au.email,1,40)) like '%%" +keywords.lower() + "%%' or lower(substring(au.first_name || ' ' || au.last_name,1,40)) like '%%" +keywords.lower() + "%%')"
        
        contsearchsql = "" 
        if contkeywords <> "":    
            contsearchsql = " and cj.id in (select distinct contcj.id from users cont inner join auth_user contauth on contauth.id=cont.django_user_id inner join contracts_application contapp on contapp.applicant_id=cont.id  inner join contracts_job contcj on contcj.id=contapp.job_id  where (lower(substring(contauth.email,1,40)) like '%%" +contkeywords.lower() + "%%' or  lower(substring(contauth.first_name || ' ' || contauth.last_name,1,40)) like '%%" +contkeywords.lower() + "%%') ) "
       
        skillsearchsql = "" 
        if skillkeywords <> "":    
            skillsearchsql = " and  ss.name like '%%" +skillkeywords.lower() + "%%'  " 
       
        budgetsql = "COALESCE(case when effort_unit=1 then budget  else 0 end, 0) as fixedbudget, COALESCE(case when effort_unit=5 then case  when budget_range=1 then '1-100'  when budget_range=2 then '101-250'  when budget_range=3 then '251-1000'  when budget_range=4 then '1001-2000' when budget_range=5 then '2001-5000' when budget_range=6 then '5000+'  when budget_range=7 then null  else null end else null end,'0') as budgetrange "
        
        sql = ("select u.id,au.first_name || ' ' || au.last_name as employer_name,au.email as Employer_Email, u.countrycode || ' ' || u.areacode || ' ' || u.mobile as phone, cj.id as job_id,substring(cj.title,1,200) as job_title,substring(to_char(cj.created_at,'YYYY-MM-DD HH24:MI:SS'),1,16) as created_at, "+budgetsql+" ,count(distinct ca.id) as application_count, count( distinct case when ca.shortlisted=true then ca.id else null end) as shortlisted, count(distinct case when cm.from_applicant=true then cm.id else null end) as applicant_messages, count(distinct case when cm.from_applicant=false then cm.id else null end) as employer_responses,count(distinct cp.message_ptr_id) as proposal_count, count(distinct case when cp.status=4 then cp.message_ptr_id else null end) as acceptedproposal_count, case when cj.status=1 then True when cj.status=2 then False end as JobStatus from contracts_job cj left outer join contracts_application ca   on cj.id=ca.job_id left outer join contracts_message cm on cm.application_id=ca.id left outer join contracts_proposal cp on cp.message_ptr_id=cm.id inner join users u on u.id=cj.employer_id inner join auth_user au on u.django_user_id=au.id left outer join contracts_requiredskill cr on cr.job_id=cj.id left outer join skills_skill ss on ss.id=cr.skill_id where created_at>='"+t1+"' and created_at<='"+t2+"' "+searchsql+ contsearchsql+ skillsearchsql +" group by employer_name,cj.id,job_title,cj.created_at,au.email,phone,u.id order by cj.created_at desc;")
        
        print sql
        results = customQuery(sql,1)
                              
        c = Context({'statistics': results})
   
        return HttpResponse(render_to_string('jobs_applications_statistics.json', c, context_instance=RequestContext(request)), mimetype='application/json') 



@csrf_exempt 
def jobs_communications_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)
        print objs
        job_id = objs['job_id']
        #print job_id;
        
        sql = ("select u.id,au.email,au.first_name || ' ' || au.last_name as freelancer_name, u.countrycode || ' ' || u.areacode || ' ' || u.mobile as phone,ca.id as application_id,case when ca.shortlisted=true then 1 else 0 end as shortlisted,count(cp.message_ptr_id) as proposals, sum(case when cp.status=4 then 1 else 0 end) as acceptedproposal_count, sum(case when cm.from_applicant=false then 1 else 0 end) as employer_responses from contracts_application ca inner join users u on u.id=ca.applicant_id inner join auth_user au on u.django_user_id=au.id inner join contracts_message cm on cm.application_id=ca.id left outer join contracts_proposal cp on cp.message_ptr_id=cm.id where job_id= "+job_id+" group by u.id,au.email,freelancer_name, phone, ca.id,shortlisted ;")
        
        print sql
        results = customQuery(sql,1)
 	print results	
        c = Context({'messages': results})
        return HttpResponse(render_to_string('jobs_communications.json', c, context_instance=RequestContext(request)), mimetype='application/json')             
        


@login_required(login_url='/accounts/login/')
def sign_job_proposal_invoice(request):
    
    t = loader.get_template('./reports/sign_job_proposal_invoice.html')
    param = get_sourceliststring()
    c = Context({'sign_job_proposal_invoice': dashboard,'param' : param  })
    return render_to_response('./reports/sign_job_proposal_invoice.html',c, context_instance=RequestContext(request))        
        
@csrf_exempt  
def sign_job_proposal_invoice_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)
        #print objs
        print objs
        cpcchecked = objs['cpcchecked']
        checkedItems = objs['checkedItems']
        signupchecked = objs['signupchecked']
        t1 = objs['fromdate']
        t2= objs['todate']
        
        wheresql = ""
        if cpcchecked== "True":
            wheresql= " Where au.date_joined >= '"+t1+"' and au.date_joined <= '"+t2+"' and u.id in " +  getcpcGroupNewAndOld(checkedItems)
        else:
            wheresql = "Where au.date_joined >= '"+t1+"' and au.date_joined <= '"+t2+"'"
           
     
        sql = ("select * from (select count(distinct au.email) as signed_up, count(distinct jobsposted.id) as posted_jobs, count(distinct paidproposal.id) as paid_proposal, count(distinct invoices.applicant_id) as invoices_paid, count(distinct jobsposted.jobid) as jobscount, count(distinct paidproposal.proposalid) as proposalscount, count(distinct invoices.invoiceid) as invoicescount  from users u inner join auth_user au on u.django_user_id=au.id  left outer join (select u1.id,cj.id as jobid from users u1 inner join contracts_job cj on cj.employer_id= u1.id) jobsposted on jobsposted.id=u.id left outer join (select u2.id,cp2.message_ptr_id as proposalid from users u2 inner join contracts_application ca2 on ca2.applicant_id=u2.id inner join contracts_message cm2 on cm2.application_id=ca2.id inner join contracts_proposal cp2 on cp2.message_ptr_id=cm2.id where cp2.status=4) paidproposal on paidproposal.id=u.id left outer join (select distinct ca1.job_id,ci.status,ci.message_ptr_id  as invoiceid,ca1.applicant_id from contracts_invoice ci inner join contracts_message cm1 on cm1.id=ci.message_ptr_id inner join contracts_application ca1 on ca1.id=cm1.application_id where ci.status=4) invoices on invoices.applicant_id=u.id " + wheresql +") total ")
        
        print sql              
        #print getcpcGroupNewAndOld()
        results = customQuery(sql,0)	
        c = Context({'statistics': results})
        return HttpResponse(render_to_string('sign_job_proposal_invoice.json', c, context_instance=RequestContext(request)), mimetype='application/json')                   
        
        dashboard
@login_required(login_url='/accounts/login/')        
def sign_application_proposal_invoice(request):
    
    t = loader.get_template('./reports/sign_application_proposal_invoice.html')
    param = get_sourceliststring()
    
    c = Context({'sign_application_proposal_invoice': dashboard, 'param' : param  })
    return render_to_response('./reports/sign_application_proposal_invoice.html',c, context_instance=RequestContext(request))        
        
@csrf_exempt  
def sign_application_proposal_invoice_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)
        #print objs
        
        cpcchecked = objs['cpcchecked']
        checkedItems = objs['checkedItems']
        signupchecked = objs['signupchecked']
        t1 = objs['fromdate']
        t2= objs['todate']        
        wheresql = ""
        if cpcchecked== "True":
            wheresql= " Where au.date_joined >= '"+t1+"' and au.date_joined <= '"+t2+"' and u.id in " +  getcpcGroupNewAndOld(checkedItems)
        else:
            wheresql = "Where au.date_joined >= '"+t1+"' and au.date_joined <= '"+t2+"'"

           
        sql = ("select count(distinct u.id) as user_count, count(distinct applicants.id) as applicants_count, count(distinct proposals.applicant_id) as proposal_count, count(distinct invoices.applicant_id) as invoice_count, count(distinct applicants.applicationid) as applicationscount, count(distinct proposals.proposalid) as proposalscount, count(distinct invoiceid) as invoicescount from users u inner join auth_user au on u.django_user_id=au.id left outer join (select u1.id,ca.id as applicationid from users u1 inner join contracts_application ca on ca.applicant_id=u1.id) applicants on applicants.id=u.id left outer join (select ca1.applicant_id,ca1.id,cp.message_ptr_id  as proposalid from contracts_application ca1 inner join contracts_message cm on cm.application_id=ca1.id inner join contracts_proposal cp on cp.message_ptr_id=cm.id) proposals on proposals.applicant_id=u.id left outer join (select ca2.applicant_id,ci.message_ptr_id as invoiceid from contracts_message cm1 inner join contracts_invoice ci on ci.message_ptr_id=cm1.id inner join contracts_application ca2 on ca2.id=cm1.application_id) invoices on invoices.applicant_id=u.id " + wheresql)
        
        results = customQuery(sql,0)
 	print sql	
        c = Context({'statistics': results})
        return HttpResponse(render_to_string('sign_application_proposal_invoice.json', c, context_instance=RequestContext(request)), mimetype='application/json')                   
        
        

@login_required(login_url='/accounts/login/')
def top_freelancers(request):
    
    t = loader.get_template('./reports/top_freelancers.html')
    c = Context({
        'top_freelancers': dashboard,
    })
    return render_to_response('./reports/top_freelancers.html', context_instance=RequestContext(request))   

@csrf_exempt
def top_freelancers_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)
        print objs
        
        priority = objs['priority']
        limit = objs['limit']
        searchaql = objs['searchkeywords']
        #t1 = objs['fromdate']  + ' 00:00:00+00'
        #t2 = objs['todate'] + ' 23:59:59+00'
        print priority;
        #keywords = objs['searchkeywords']
        sortsql = ""
        if priority== "Skills Count":
            sortsql= " order by skillscount desc"
        elif priority=="Profile Completion":
            sortsql= " order by profilecompletion desc"
        else:
            sortsql= " order by applicationcount  desc"    

        #print sortsql   
        sql = ("select distinct u.id,au.first_name || ' ' || au.last_name as fullname,au.email, u.countrycode || ' ' || u.areacode || ' ' || u.mobile, case when (u.photo <>'' and u.photo is not null) then 'https://nabbesh-images.s3.amazonaws.com/' || replace(u.photo,'/','') else 'http://www.nabbesh.com/static/images/thumb.png' end as photo, usercountry, round(((addedskills::float+hasphoto::float+hasbio::float+employment::float+education::float+visual::float)*100/6)::numeric,0) as profilecompletion,skillscount, applicationcount from users u inner join auth_user au on u.django_user_id=au.id inner join ( select u.id as userid ,u.country as usercountry, case when count(distinct su.skill_id)>0 then 1 else 0 end as addedskills, count(distinct su.skill_id) as skillscount, case when (u.photo is not null and u.photo<>'') then 1 else 0 end as hasphoto, case when (u.bio is not null and u.bio <>'') then 1 else 0 end as hasbio, case when count(distinct ce.id)> 0 then 1 else 0 end as employment, case when count(distinct edu.id)>0 then 1 else 0 end as education, case when count(distinct ct.id)>0 then 1 else 0 end as visual, count(distinct ca.id) as applicationcount from users u inner join auth_user au on u.django_user_id=au.id left outer join skills_users su on su.id_user=u.id left outer join education edu on edu.id_user=u.id inner join canvas_box cb on cb.profile_id=u.id left outer join canvas_employment ce on ce.box_id=cb.id left outer join canvas_thumbnail ct on ct.box_id=cb.id inner join contracts_application ca on ca.applicant_id=u.id group by u.id) total on total.userid=u.id inner join skills_users su1 on su1.id_user=u.id inner join skills_skill ss1 on ss1.id=su1.skill_id where lower(ss1.name) like '%%"+searchaql +"%%'"+ sortsql + " limit "+ limit)
        
        
        print sql
        results = customQuery(sql,0)
 	#print results	
        c = Context({'users': results})
        return HttpResponse(render_to_string('top_freelancers.json', c, context_instance=RequestContext(request)), mimetype='application/json')             

@login_required(login_url='/accounts/login/')
def top_employers(request):
    
    t = loader.get_template('./reports/top_employers.html')
    c = Context({
        'top_employers': dashboard,
    })
    #return HttpResponse(t.render(c))   
    return render_to_response('./reports/top_employers.html', context_instance=RequestContext(request))

@csrf_exempt 
def top_employers_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)
        print objs
        limit = objs['limit']
        priority = objs['priority']
        
        sortsql = ""
        if priority== "Jobs Count":
            sortsql= " order by jobs_count"
        else:
            sortsql= " order by accepted_proposals_count"

        
        sql = ("select u.id, au.first_name || ' ' || au.last_name as fullname , au.email, u.countrycode || ' ' || u.areacode || ' ' || u.mobile, 'http://www.nabbesh.com/profile/' || u.id as homepage, case when (u.photo <>'' and u.photo is not null) then 'https://nabbesh-images.s3.amazonaws.com/'  || replace(u.photo,'/','') else 'http://www.nabbesh.com/static/images/thumb.png' end  as photo, u.country, count(distinct cj.id) as jobs_count, count(distinct applications.proposal_id) as accepted_proposals_count from users u inner join auth_user au on u.django_user_id=au.id  left outer join contracts_job cj on cj.employer_id=u.id   left outer join ( select distinct cj1.employer_id,cm1.id as proposal_id from contracts_job cj1 inner join contracts_application ca1 on ca1.job_id=cj1.id inner join contracts_message cm1 on cm1.application_id=ca1.id  inner join contracts_proposal cp1 on cp1.message_ptr_id=cm1.id where cp1.status=4) applications on applications.employer_id=u.id group  by u.id,au.email,fullname,photo,homepage  "+sortsql+"  desc limit " + limit)
        
        print sql
        results = customQuery(sql,0)
 	#print results	
        c = Context({'users': results})
        return HttpResponse(render_to_string('top_employers.json', c, context_instance=RequestContext(request)), mimetype='application/json')  
        
        


@login_required(login_url='/accounts/login/')       
def skillsdemography_report(request):
    
    t = loader.get_template('./reports/skillsdemography_report.html')
    c = Context({
        'skillsdemography_report': freelancerdemography_report,
    })
   
    #return HttpResponse(t.render(c))
    return render_to_response('./reports/skillsdemography_report.html', context_instance=RequestContext(request))
    
    
    
@csrf_exempt
def skillsdemography_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)
        limit = objs['limit']
        priority = objs['priority']
        
             
        sortsql="users_have_it"
        if priority=="Users Count":
            sortsql="users_have_it"
        elif priority=="Users Country Count":
            sortsql="countries_users"
        elif priority=="Jobs Count":
            sortsql="jobs_require_it"
        elif priority=="Jobs Country Count":
            sortsql="countries_jobs"
        
        sql = ("select skills.name, calc.*, case when calc.jobs_require_it<>0 then cast(calc.users_have_it as real)/cast(calc.jobs_require_it as real) else 0 end as availability_rate from skills_skill skills inner join (select ss.id, count(distinct su.id_user)  as users_have_it, count(distinct u1.country) as countries_users, count(distinct crs.job_id) as jobs_require_it, count(distinct u2.country) as countries_jobs from skills_skill ss left outer join skills_users su on su.skill_id=ss.id inner join users u1 on su.id_user=u1.id left outer join contracts_requiredskill crs on crs.skill_id=ss.id inner join contracts_job cj on cj.id=crs.job_id inner join users u2 on u2.id=cj.employer_id where ss.deleted=false group by ss.id) calc on calc.id=skills.id order by "+sortsql+" desc limit "+ limit)
        
        print sql 
        results = customQuery(sql,0)
    
        c = Context({'countries': results})
   
        return HttpResponse(render_to_string('skillsdemography.json', c, context_instance=RequestContext(request)), mimetype='application/json')           
        


 
        
        
@csrf_exempt
def skillsdemographydetails_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)
        skill_id= objs['skill_id']
        sql = ("select country, jobs_count,users_count, case when jobs_count<>0 then cast(users_count as real)/cast(jobs_count as real) else 0 end as availability_rate from  (select case when total1.country is not null then total1.country else total2.country end as country, case when total1.jobs_count is not null then total1.jobs_count else 0 end as jobs_count, case when total2.users_count is not null then total2.users_count else 0 end as users_count from ( select count(*) as jobs_count,u.country  from contracts_job cj  inner join users u on cj.employer_id=u.id  inner join contracts_requiredskill crs on crs.job_id=cj.id where crs.skill_id= "+skill_id +" group by u.country) total1 full outer join  (select count(*) as users_count, u.country  from users u  inner join skills_users su on su.id_user=u.id where su.skill_id="+skill_id+" group by u.country) total2 on total1.country=total2.country ) total")
 
        results = customQuery(sql,0)

        c = Context({'countries': results})
   
        return HttpResponse(render_to_string('skillsdemographydetails.json', c, context_instance=RequestContext(request)), mimetype='application/json')           
            

@login_required(login_url='/accounts/login/')        
def skillsdistribution_report(request):
    
    t = loader.get_template('./reports/skillsdistribution_report.html')
    c = Context({
        'skillsdistribution_report': freelancerdemography_report,
    })
   
    return render_to_response('./reports/skillsdistribution_report.html', context_instance=RequestContext(request))

    
    
@csrf_exempt
def skillsdistribution_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)
        limit = objs['limit']
        priority = objs['priority']
        
        searchkeywords = objs['searchkeywords']     
        
        searchsql = ""
        if searchkeywords <> "":
            searchsql = "and lower(name) like '%%" +searchkeywords.lower() + "%%'"
        
        
        sortsql="userscount"
        if priority=="Users Count":
            sortsql="userscount"        
        elif priority=="Jobs Count":
            sortsql="jobscount"
       
        
        sql = ("select *, case when jobscount<>0 then cast(userscount as real)/cast(jobscount as real) else 0 end as availability_rate  from (select * from (select ss.id, ss.name,count(distinct su.id_user) as userscount, count( distinct cr.job_id) as jobscount  from skills_skill ss left outer join skills_users su on ss.id=su.skill_id left outer join contracts_requiredskill cr on cr.skill_id=ss.id where ss.deleted<>true and ss.published=true and ss.merge_to_id is null group by ss.id ) total where (jobscount<>0 or userscount<>0) "+searchsql+" order by "+sortsql+" desc limit "+limit+") total")
        
        
        print sql
        results = customQuery(sql,0)     
        c = Context({'countries': results})
        
        return HttpResponse(render_to_string('skillsdistribution.json', c, context_instance=RequestContext(request)), mimetype='application/json') 


@csrf_exempt        
def geocodes(request):
    
    t = loader.get_template('./geocodes.json')
    c = Context({
        'geocodes': geocodes,
    })
    return HttpResponse(t.render(c))
            
            
@login_required(login_url='/accounts/login/')        
def crosscountryapps_report(request):
    
    t = loader.get_template('./reports/crosscountryapps_report.html')
    c = Context({
        'crosscountryapps_report': crosscountryapps_report,
    })
    return render_to_response('./reports/crosscountryapps_report.html', context_instance=RequestContext(request))
            
@csrf_exempt
def crosscountryapps_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)
        grouplevel= objs['grouplevel']
        limit = objs['limit']
        colsql = 'applicants.country as appcountry, applicants.city as appcity,employers.country as empcountry, employers.city as empcity'
        groupsql = 'group by empcountry,empcity,appcountry,appcity'
        if grouplevel == 'Country':
            colsql = 'applicants.country as appcountry,employers.country as empcountry'
            groupsql = 'group by empcountry,appcountry'
            
        sql = ("select *, count(*) as appcount from  (select "+ colsql +" from users applicants  inner join contracts_application ca on ca.applicant_id=applicants.id  inner join contracts_job cj on cj.id=ca.job_id  inner join users employers on employers.id=cj.employer_id where employers.country<>applicants.country) total  where empcountry<>'' and appcountry<>'' " + groupsql + " order by appcount desc limit "+ limit)
 
        results = customQuery(sql,0)

        c = Context({'lines': results})
        if grouplevel=='Country':
	    return HttpResponse(render_to_string('crosscountryapps.json', c, context_instance=RequestContext(request)), mimetype='application/json')           
	else:
	    return HttpResponse(render_to_string('crosscityapps.json', c, context_instance=RequestContext(request)), mimetype='application/json')           
	    
            
                        
@login_required(login_url='/accounts/login/')         
def proposals_report(request):
    
    t = loader.get_template('./reports/proposals_report.html')
    c = Context({
        'proposals_report': proposals_report,
    })
    return render_to_response('./reports/proposals_report.html', context_instance=RequestContext(request))
            
@csrf_exempt
def proposals_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)         
        t1 = objs['fromdate'] + ' 00:00:00+00'
        t2 = objs['todate']  + ' 23:59:59+00'
        grouper="7"
        groupertext = objs['grouper']    
        if groupertext=="Year":
            grouper="4"
        elif groupertext=="Month":
            grouper="7"
        elif groupertext=="Day": 
            grouper="10"             
            
                  
        sql = ("select substring(to_char(cm.timestamp,'YYYY-MM-DD HH24:MI:SS'),1, "+grouper+") as sentat, COALESCE(sum(case when cp.status=1 then cp.deposit_amount end),0) as New, count(case when cp.status=1 then 1 end) as NewCount, round(COALESCE(avg(case when cp.status=1 then cp.deposit_amount end),0),2) as NewAvg, COALESCE(sum(case when cp.status=2 then cp.deposit_amount end),0) as Canceled, count(case when cp.status=2 then 1 end) as CanceledCount, round(COALESCE(avg(case when cp.status=2 then cp.deposit_amount end),0),2) as CanceledAvg, COALESCE(sum(case when cp.status=3 then cp.deposit_amount end),0) as Declined, count(case when cp.status=3 then 1 end) as DeclinedCount, round(COALESCE(avg(case when cp.status=3 then cp.deposit_amount end),0),2) as Avg, COALESCE(sum(case when cp.status=4 then cp.deposit_amount end),0) as Accepted, count(case when cp.status=4 then 1 end) as AcceptedCount, round(COALESCE(avg(case when cp.status=4 then cp.deposit_amount end),0),2) as AcceptedAvg from contracts_proposal cp inner join contracts_message cm on cm.id=cp.message_ptr_id where cm.timestamp>='"+t1+"' and cm.timestamp<='"+t2+"'  group  by sentat order by sentat ") 
        results = customQuery(sql,0)
        c = Context({'proposals': results})        
	return HttpResponse(render_to_string('proposals.json', c, context_instance=RequestContext(request)), mimetype='application/json')           
	


@login_required(login_url='/accounts/login/')        
def invoices_report(request):
    
    t = loader.get_template('./reports/invoices_report.html')
    c = Context({
        'invoices_report': invoices_report,
    })
    return render_to_response('./reports/invoices_report.html', context_instance=RequestContext(request))
            
@csrf_exempt
def invoices_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)         
        t1 = objs['fromdate'] + ' 00:00:00+00'
        t2 = objs['todate']  + ' 23:59:59+00'
        grouper="7"
        groupertext = objs['grouper']    
        if groupertext=="Year":
            grouper="4"
        elif groupertext=="Month":
            grouper="7"
        elif groupertext=="Day": 
            grouper="10"             
            
                  
        sql = ("select  substring(to_char(cm.timestamp,'YYYY-MM-DD HH24:MI:SS'),1, "+grouper+") as sentat, round(COALESCE(sum(case when ci.status=1 then quantity * unit_price end),0,2)) as NewAmount, count(case when ci.status=1 then 1 end) as NewCount, round(COALESCE(avg(case when ci.status=1 then quantity * unit_price end),0,2)) as NewAverage, round(COALESCE(sum(case when ci.status=2 then quantity * unit_price end),0,2)) as CancelledAmount, count(case when ci.status=2 then 1 end) as CancelledCount, round(COALESCE(avg(case when ci.status=2 then quantity * unit_price end),0,2)) as CancelledAverage, round(COALESCE(sum(case when ci.status=3 then quantity * unit_price end),0,2)) as DeclinedAmount, count(case when ci.status=3 then 1 end) as DeclinedCount, round(COALESCE(avg(case when ci.status=3 then quantity * unit_price end),0,2)) as DeclinedAverage, round(COALESCE(sum(case when ci.status=4 then quantity * unit_price end),0,2)) as PaidAmount, count(case when ci.status=4 then 1 end) as PaidCount, round(COALESCE(avg(case when ci.status=4 then quantity * unit_price end),0,2)) as PaidAverage  from contracts_invoice ci  inner join contracts_invoiceitem cii on cii.invoice_id=ci.message_ptr_id  inner join contracts_message cm on cm.id=ci.message_ptr_id  where cm.timestamp>='"+t1+"' and cm.timestamp<='"+t2+"' group by sentat  order by sentat ") 
        results = customQuery(sql,0)
        c = Context({'invoices': results})        
	return HttpResponse(render_to_string('invoices.json', c, context_instance=RequestContext(request)), mimetype='application/json')           
	
            
            
@login_required(login_url='/accounts/login/')
def jobs_apps_stats_report(request):
    
    t = loader.get_template('./reports/jobs_apps_stats_report.html')
    c = Context({
        'jobs_apps_stats_report': jobs_apps_stats_report,
    })
    return render_to_response('./reports/jobs_apps_stats_report.html', context_instance=RequestContext(request))
            
@csrf_exempt
def jobs_apps_stats_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)         
        t1 = objs['fromdate'] + ' 00:00:00+00'
        t2 = objs['todate']  + ' 23:59:59+00'
        grouper="7"
        groupertext = objs['grouper']    
        if groupertext=="Year":
            grouper="4"
        elif groupertext=="Month":
            grouper="7"
        elif groupertext=="Day": 
            grouper="10"             
            
                  
        sql = ("select substring(to_char(created_at,'YYYY-MM-DD HH24:MI:SS'),1, "+grouper+")as createdat,count(*) as total, count(case when appscount = 0 then 1 end) as count_0, count(case when (appscount >= 1) and (appscount<=5) then 1 end) as count_1_5,  count(case when (appscount > 5) and (appscount<=10) then 1 end) as count_6_10, count(case when (appscount > 10) and (appscount<=50) then 1 end) as count_11_50, count(case when (appscount > 50) then 1 end) as count_more_50   from (select  cj.id as jobid,cj.created_at, count(distinct ca.id) as appscount from contracts_job cj left outer join contracts_application ca on ca.job_id = cj.id where created_at>='"+t1+"' and created_at<='"+t2+"' group by jobid,cj.created_at) total group by createdat order by createdat") 
        
        print sql
        results = customQuery(sql,0)
        c = Context({'jobs_apps_stats': results})        
	return HttpResponse(render_to_string('jobs_apps_stats.json', c, context_instance=RequestContext(request)), mimetype='application/json')           



@login_required(login_url='/accounts/login/')       
def signups_apps_retention_report(request):
    
    t = loader.get_template('./reports/signups_apps_retention_report.html')
    c = Context({
        'signups_apps_retention_report': signups_apps_retention_report,
    })
    return render_to_response('./reports/signups_apps_retention_report.html', context_instance=RequestContext(request))
            
@csrf_exempt
def signups_apps_retention_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)                              
        n=int(objs['period'])
        m=int(objs['month'])     
        dynsql1=""
        dynsql2=""
        for i in range(1,n+1):             
            dynsql1 = dynsql1 + ", round((month"+str(i)+"::float * 100.00 /totalsignup::float)::numeric,2) as applied_month"+str(i)
            dynsql2 = dynsql2 + ",count(distinct case when timestamp >=(date_joined + INTERVAL '"+str(m*(i-1))+" Month') and timestamp <=(date_joined + INTERVAL '"+str(m*i)+" Month') then id else null end) as month"+str(i)
        sql = ("select datejoined,totalsignup "+dynsql1+" from (select substring(to_char(date_joined,'YYYY-MM-DD'),1,4) || '-' || to_char((cast(substring(to_char(date_joined,'YYYY-MM-DD'),6,2) as int)-1)/"+str(m)+"+1,'09') || ' pr' as datejoined,count(distinct id) as totalsignup "+dynsql2+"  from (select u.id,au.date_joined, ca.timestamp from users u inner join auth_user au on u.django_user_id=au.id left outer join contracts_application ca on ca.applicant_id=u.id) total group by datejoined order by datejoined desc) final ") 
        results = customQuery(sql,0)
        c = Context({'signups_apps_retention': results,'n' : xrange(n)})        
	return HttpResponse(render_to_string('signups_apps_retention.json', c, context_instance=RequestContext(request)), mimetype='application/json')           
	           


@login_required(login_url='/accounts/login/')        
def signups_jobs_retention_report(request):
    
    t = loader.get_template('./reports/signups_jobs_retention_report.html')
    c = Context({
        'signups_jobs_retention_report': signups_jobs_retention_report,
    })
    return render_to_response('./reports/signups_jobs_retention_report.html', context_instance=RequestContext(request))
            
@csrf_exempt
def signups_jobs_retention_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)         
                     
        n=int(objs['period'])
        m=int(objs['month']) 

        dynsql1=""
        dynsql2=""
        for i in range(1,n+1):    
            dynsql1 = dynsql1 + ", round((month"+str(i)+"::float * 100.00 /totalsignup::float)::numeric,2) as applied_month"+str(i)      
            dynsql2 = dynsql2 + ", count(distinct case when created_at >=(date_joined + INTERVAL '"+ str(m*(i-1))+" Month') and created_at <=(date_joined + INTERVAL '"+str(m*i) +" Month') then id else null end) as month"+str(i)
                         
        sql = ("select datejoined,totalsignup "+dynsql1+" from ( select substring(to_char(date_joined,'YYYY-MM-DD'),1,4) || '-' || to_char((cast(substring(to_char(date_joined,'YYYY-MM-DD'),6,2) as int)-1)/"+str(m)+"+1,'09') || ' pr' as datejoined, count(distinct id) as totalsignup "+dynsql2+"  from  ( select u.id,au.date_joined, cj.created_at from  users u  inner join auth_user au on u.django_user_id=au.id left outer join contracts_job cj on cj.employer_id=u.id) total  group by datejoined order by datejoined desc  ) final ") 
        
        
        results = customQuery(sql,0)
        print sql
        print results
        c = Context({'signups_jobs_retention': results,'n' : xrange(n)})        
	return HttpResponse(render_to_string('signups_jobs_retention.json', c, context_instance=RequestContext(request)), mimetype='application/json')     
	           



@login_required(login_url='/accounts/login/')       
def jobs_apps_retention_report(request):
    
    t = loader.get_template('./reports/jobs_apps_retention_report.html')
    c = Context({
        'jobs_apps_retention_report': jobs_apps_retention_report,
    })
    return render_to_response('./reports/jobs_apps_retention_report.html', context_instance=RequestContext(request))
            
@csrf_exempt
def jobs_apps_retention_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)         
                    
        n=int(objs['period'])
        m=int(objs['month'])      
        dynsql1=""
        dynsql2=""
        for i in range(1,n+1): 
            dynsql1 = dynsql1 + ", round((month"+str(i)+"::float * 100.00 /totaljobs::float)::numeric,2) as receivedapp_month" + str(i)
            dynsql2 = dynsql2 + ", count(distinct case when timestamp >=(created_at + INTERVAL '"+str(m*(i-1))+" Month') and timestamp <=(created_at + INTERVAL '"+str(m*i)+" Month') then id else null end) as month"+str(i)

        sql = ("select datejoined,totaljobs " +dynsql1+ " from (select substring(to_char(created_at,'YYYY-MM-DD'),1,4) || '-' || to_char((cast(substring(to_char(created_at,'YYYY-MM-DD'),6,2) as int)-1)/"+str(m)+"+1,'09') || ' pr' as datejoined, count(distinct id) as totaljobs "+ dynsql2 +"  from  ( select cj.id as id, cj.created_at, ca.timestamp from contracts_job cj left outer join contracts_application ca on ca.job_id=cj.id ) total group by datejoined order by datejoined desc) final") 
        results = customQuery(sql,0)
                                   
        c = Context({'jobs_apps_retention': results,'n' : xrange(n)})        
	return HttpResponse(render_to_string('jobs_apps_retention.json', c, context_instance=RequestContext(request)), mimetype='application/json') 




@login_required(login_url='/accounts/login/')         
def activities_countries_report(request):
    
    t = loader.get_template('./reports/activities_countries_report.html')
    c = Context({
        'activities_countries_report': jobs_apps_retention_report,
    })
    return render_to_response('./reports/activities_countries_report.html',c, context_instance=RequestContext(request))
            
@csrf_exempt
def activities_countries_getdata(request):
    if request.method == 'POST':
        #objs = simplejson.loads(request.raw_post_data)         

        sql = ("select distinct u.country, COALESCE(usercount,0) as usercount, COALESCE(jobscount,0) as jobscount, COALESCE(appscount,0) as appscount, COALESCE(proposalcount,0) as proposalcount, COALESCE(invoicecount,0) as invoicecount from users u left outer join (select count(distinct u.id) as usercount, u.country from users u inner join auth_user au on u.django_user_id=au.id group by u.country ) signups on signups.country=u.country left outer join (select count(distinct cj.id) as jobscount,u.country  from contracts_job cj inner join users u on u.id=cj.employer_id  group by u.country) jobs on jobs.country=u.country left outer join (select count(distinct ca.id) as appscount, u.country from contracts_application ca inner join users u on u.id=ca.applicant_id  group by u.country) apps on apps.country=u.country left outer join (select count(distinct cm.id) as proposalcount, u.country from contracts_proposal cp inner join contracts_message cm on cm.id=cp.message_ptr_id inner join contracts_application ca on ca.id=cm.application_id inner join users u on u.id=ca.applicant_id group by u.country) proposals on proposals.country=u.country left outer join (select count(distinct cm.id) as invoicecount, u.country from contracts_invoice ci inner join contracts_message cm on cm.id=ci.message_ptr_id inner join contracts_application ca on ca.id=cm.application_id inner join users u on u.id=ca.applicant_id  group by u.country) invoices on invoices.country=u.country where u.country is not null and u.country<>'' order by usercount desc") 
        print sql
        results = customQuery(sql,0)
        
       
        print results                           
        c = Context({'countries': results})        
	return HttpResponse(render_to_string('activities_countries.json', c, context_instance=RequestContext(request)), mimetype='application/json') 




@login_required(login_url='/accounts/login/')
def payers_report(request):
    
    t = loader.get_template('./reports/payers_report.html')
    c = Context({
        'payers_report': payers_report,
    })
    return render_to_response('./reports/payers_report.html', context_instance=RequestContext(request))
            
@csrf_exempt
def payers_getdata(request):
    if request.method == 'POST':
        #objs = simplejson.loads(request.raw_post_data)

        sql = "select distinct u.id,au.first_name || ' ' || au.last_name as fullname, au.email, u.country,cj.id,substring(to_char(cj.created_at,'YYYY-MM-DD HH24:MI:SS'),1,16), cj.title, cii.quantity*cii.unit_price as amount from users u  inner join auth_user au on au.id=u.django_user_id inner join contracts_job cj on cj.employer_id=u.id  inner join contracts_application ca on ca.job_id = cj.id inner join contracts_message cm on cm.application_id=ca.id inner join contracts_invoice ci on ci.message_ptr_id=cm.id inner join contracts_invoiceitem  cii on cii.invoice_id=ci.message_ptr_id where ci.status=4 "
        
        print sql
        results = customQuery(sql,0)
        print results
 
        c = Context({'payers': results})
   
        return HttpResponse(render_to_string('payers.json', c, context_instance=RequestContext(request)), mimetype='application/json')



@login_required(login_url='/accounts/login/')
def payees_report(request):
    
    t = loader.get_template('./reports/payees_report.html')
    c = Context({
        'payees_report': payers_report,
    })
    return render_to_response('./reports/payees_report.html', context_instance=RequestContext(request))
            
@csrf_exempt
def payees_getdata(request):
    if request.method == 'POST':
        #objs = simplejson.loads(request.raw_post_data)

        sql = "select  distinct u.id,  au.first_name || ' ' || au.last_name as fullname,  au.email, u.country,cj.id, substring(to_char(cj.created_at,'YYYY-MM-DD HH24:MI:SS'),1,16),   cj.title, cii.quantity*cii.unit_price as amount   from users u    inner join auth_user au on au.id=u.django_user_id   inner join contracts_application ca on ca.applicant_id = u.id  inner join contracts_job cj on cj.id=ca.job_id  inner join contracts_message cm on cm.application_id=ca.id   inner join contracts_invoice ci on ci.message_ptr_id=cm.id   inner join contracts_invoiceitem  cii on cii.invoice_id=ci.message_ptr_id where ci.status=4  "
        
        print sql
        results = customQuery(sql,0)
        print results
 
        c = Context({'payees': results})
   
        return HttpResponse(render_to_string('payees.json', c, context_instance=RequestContext(request)), mimetype='application/json')


@login_required(login_url='/accounts/login/')
def payments_report(request):
    
    t = loader.get_template('./reports/payments_report.html')
    c = Context({
        'payments_report': payments_report,
    })
    return render_to_response('./reports/payments_report.html', context_instance=RequestContext(request))
            
@csrf_exempt
def payments_getdata(request):
    if request.method == 'POST':
        #objs = simplejson.loads(request.raw_post_data)

        sql = " select distinct  payer.id, aupayer.first_name || ' ' || aupayer.last_name as payerfullname, aupayer.email,  payer.country,   cj.id, substring(to_char(cj.created_at,'YYYY-MM-DD HH24:MI:SS'),1,16),  cj.title, sum( cii.quantity*cii.unit_price )as amount ,  payee.id, aupayee.first_name || ' ' || aupayee.last_name as payeefullname, aupayee.email,  payee.country       from users payee   inner join auth_user aupayee on aupayee.id=payee.django_user_id    inner join contracts_application ca on ca.applicant_id = payee.id    inner join contracts_job cj on cj.id=ca.job_id    inner join users payer on payer.id=cj.employer_id  inner join auth_user aupayer on aupayer.id=payer.django_user_id  inner join contracts_message cm on cm.application_id=ca.id  inner join contracts_invoice ci on ci.message_ptr_id=cm.id  inner join contracts_invoiceitem  cii on cii.invoice_id=ci.message_ptr_id  where ci.status=4   group by payer.id,payerfullname, aupayer.email, payer.country, cj.id, cj.created_at, payee.id, payeefullname, aupayee.email, payee.country  "
        
        print sql
        results = customQuery(sql,0)
        print results
 
        c = Context({'payments': results})
   
        return HttpResponse(render_to_string('payments.json', c, context_instance=RequestContext(request)), mimetype='application/json')





@login_required(login_url='/accounts/login/')
def revenue_report(request):
    
    t = loader.get_template('./reports/revenue_report.html')
    c = Context({
        'revenue_report': revenue_report,
    })
    return render_to_response('./reports/revenue_report.html', context_instance=RequestContext(request))
            
@csrf_exempt
def revenue_getdata(request):
    if request.method == 'POST':

        objs = simplejson.loads(request.raw_post_data)
        #print objs
        
        t1 = objs['fromdate'] + ' 00:00:00+00'
        t2 = objs['todate']  + ' 23:59:59+00'
        
        grouppertext= objs['limit']
        sql = "select "+datefieldtostring("cm.timestamp", grouppertext) + " as msgdate, count(distinct cp.message_ptr_id) as proposals, count(distinct case when cp.status=4 then cp.message_ptr_id else null end) as acceptedproposals, sum(distinct case when cp.status=4 then cp.deposit_amount else 0 end) as escrow, count(distinct ci.message_ptr_id) as invoices, count(distinct case when ci.status=4 then ci.message_ptr_id else null end) as paidinvoices, sum(distinct case when ci.status=4 then cii.unit_price * cii.quantity else 0 end) as invoiceamounts, sum(distinct case when ci.status=4 then cii.unit_price * quantity * 9 /100 else 0 end) as revenue from contracts_message cm left outer join contracts_proposal cp on cp.message_ptr_id=cm.id left outer join contracts_invoice ci on ci.message_ptr_id=cm.id left outer join contracts_invoiceitem cii on cii.invoice_id=ci.message_ptr_id where cm.timestamp >= '"+t1+"' and cm.timestamp <= '"+t2+"' group by msgdate order by msgdate desc"
        
        print sql
        results = customQuery(sql,0)
        print results
 
        c = Context({'revenue': results})
   
        return HttpResponse(render_to_string('revenue.json', c, context_instance=RequestContext(request)), mimetype='application/json')


@csrf_exempt 
def total_users_getdata(request):
    if request.method == 'GET':
        
        sql = ("select count(id), count(case when is_active=true then 1 else null end)  from auth_user")
        
        print sql
        results = customQuery(sql,0)
        return HttpResponse(json.dumps(results), mimetype='application/json') 
 	

@csrf_exempt     
def vistest_report(request):
    
   
    t = loader.get_template('./reports/vistest_report.html')
    c = Context({
        'vistest_report': vistest_report,
    })
    return HttpResponse(t.render(c))

def getskillname(skillid):
    result = customQuery("select name from skills_skill where id="+skillid,0)    
    return result[0][0]

def decorateelement(element):
    result = list()
    #print element
    for i,item in enumerate(element[0]):
        if i<>0:      
            result.append(str(getskillname(str(item))))            
        else:
            result.append(str(item))         
    return  result

def getskillsgrouppower(listofskills):
    result = 0
    sql = "select  "
    headers = "occurrence"
    skillids = ""
    joins = ""
    wheresql = ""
    
    for i,item  in enumerate(listofskills):
        headers = headers + ", skill" + str(i+1)
        skillids = skillids + ", su" +str(i+1) +".skill_id as skill"+str(i+1)
        if i <> 0:
            joins = joins + " inner join skills_users su"+ str(i+1) +" on su1.id_user=su"+str(i+1)+".id_user "
        
        wheresql = wheresql + " and su"+ str(i+1) + ".skill_id=" + str(item[0])
        
        
    sql = sql + headers + " from (select count(id_user) as "  + headers + " from (select  distinct su1.id_user " +  skillids + " from skills_users su1 " + joins + " where " + wheresql[4:] + "  )  total group by " + headers[12:] + " order by occurrence desc) final" 
    #print sql   
    result =  customQuery(sql,0)
    #print result
    return result
    
def list_duplicates(seq):
  seen = set()
  seen_add = seen.add
  seen_twice = set( x for x in seq if x in seen or seen_add(x) )
  return list( seen_twice )

def preparetoappend(element):
    if len(list_duplicates(element))>0:
        return False
    else:
        return True
def skillsmining(level,topskills):
    sql = "select skill_id from (select count(distinct id_user) as usercount, skill_id from skills_users group by skill_id order by usercount desc limit "+str(topskills)+" ) total"    
    skills = customQuery(sql,0)    
    params = list()
    for i in range(1,level+1):    
        params.append(skills)        
    results =  list()
    for element in itertools.product(*params):   
        if preparetoappend(element): 
            if not sorted(element) in results:                                    
                results.append(sorted(element))
               # print element
    calculatedresults = list()    
    for element in results:
        calculatedelement = getskillsgrouppower(element)
        if len(calculatedelement)>0:
            #print decorateelement(calculatedelement)
            calculatedresults.append(decorateelement(calculatedelement))
    return calculatedresults

@csrf_exempt     
def miningtest_getdata(request):       
    data = skillsmining(2,50)      
    headers = ["header1", "header2" , "headers3"]
    data.insert(0,headers)
    return HttpResponse(json.dumps(data), mimetype='application/json')  
    

@csrf_exempt     
def miningtest_report(request):
    
   
    t = loader.get_template('./reports/miningtest_report.html')
    c = Context({
        'miningtest_report': miningtest_report,
    })
    return HttpResponse(t.render(c))
    
    
@csrf_exempt
def analytics_getdata(request):
    if request.method == 'POST':
        objs = simplejson.loads(request.raw_post_data)        
        t1 = objs['fromdate']
        t2 = objs['todate']
        
        print t1,t2
        limit = objs['limit']
        print limit
        data  = ga_get_visits(t1,t2,limit)
        print data
        c = Context({'analytics': data})     
        
           
	return HttpResponse(render_to_string('analytics_visitors.json', c, context_instance=RequestContext(request)), mimetype='application/json') 
       
        
 
@csrf_exempt     
def campaigns_report(request):
    
   
    t = loader.get_template('./reports/campaigns_report.html')
    c = Context({
        'campaigns_report': campaigns_report,
    })

    return HttpResponse(t.render(c)) 
    
    
    
@csrf_exempt
def campaigns_list_getdata(request):
    listsql = "select id, concat(substring(replace(replace(title,',',''), '''',''),1,45)) , substring(cast(FROM_UNIXTIME(sent) as char),1,16), cast(recipients as char)  from campaigns order by id desc limit 25;"   
            
    campaigns = customQuery(listsql,3)
   
    #campaignstring = ""
    #for campaign in campaigns:
        #campaignstring=campaignstring+","+str(campaign[1]) 
      
    #return campaignstring[1:]    
    
    c = Context({'campaigns': campaigns})     
    return HttpResponse(render_to_string('campaignslist.json', c, context_instance=RequestContext(request)), mimetype='application/json')
 
@csrf_exempt
def campaign_opens_getdata(id):
    totalsentsql = "select recipients,  substring(cast(FROM_UNIXTIME(sent) as char),1,10) from campaigns where id="+ str(id)
    
    totalsent = customQuery(totalsentsql,3)
    openssql = "select opens from campaigns where id="+str(id)            
    openstring = customQuery(openssql,3)[0][0]             
    ids = openstring.split(',')    
    idsstring=""
    
    for id in ids:
        idsstring=idsstring+","+id[:id.index(':')]
        
    openemailssql = "select email from subscribers where id in ("  +   idsstring[1:]   + ");"   
    emails = customQuery(openemailssql,3)
    emailsstring = ""
    opencount=0
    for email in emails:
        opencount=opencount+1
        emailsstring=emailsstring+ ",'" + email[0] + "'"        
        
      
    return totalsent[0], opencount,emailsstring[1:]
    
@csrf_exempt  
def emailcampaign_getdata(request):
    if request.method == 'POST':       
        objs = simplejson.loads(request.raw_post_data)
                 
        campaignid = objs['id']      
         
        campaigninfo = campaign_opens_getdata(campaignid)
        
        
        wheresql = " where au.email in ("+ campaigninfo[2] + ")  and au.date_joined>='" +  campaigninfo[0][1] +"'"
        
        sql = ("select count(distinct u.id) as user_count, count(distinct applicants.id) as applicants_count, count(distinct proposals.applicant_id) as proposal_count, count(distinct invoices.applicant_id) as invoice_count, count(distinct applicants.applicationid) as applicationscount, count(distinct proposals.proposalid) as proposalscount, count(distinct invoiceid) as invoicescount from users u inner join auth_user au on u.django_user_id=au.id left outer join (select u1.id,ca.id as applicationid from users u1 inner join contracts_application ca on ca.applicant_id=u1.id) applicants on applicants.id=u.id left outer join (select ca1.applicant_id,ca1.id,cp.message_ptr_id  as proposalid from contracts_application ca1 inner join contracts_message cm on cm.application_id=ca1.id inner join contracts_proposal cp on cp.message_ptr_id=cm.id) proposals on proposals.applicant_id=u.id left outer join (select ca2.applicant_id,ci.message_ptr_id as invoiceid from contracts_message cm1 inner join contracts_invoice ci on ci.message_ptr_id=cm1.id inner join contracts_application ca2 on ca2.id=cm1.application_id) invoices on invoices.applicant_id=u.id " + wheresql)
        
        results = customQuery(sql,0)
 	
 	
        c = Context({'statistics': results, 'totalsent': campaigninfo[0][0], 'opens': campaigninfo[1] })
        return HttpResponse(render_to_string('emailcampaign.json', c, context_instance=RequestContext(request)), mimetype='application/json')                   
    
@csrf_exempt
def ga_get_visits_query(service,profile_id, start, end, limit):
    dims = ""
    if limit=='Month':
        dims="ga:year,ga:month"
    elif limit=="Day":
        dims="ga:year,ga:month,ga:day"
    else:
        dims="ga:year,ga:week"    
    data = service.data().ga().get(ids="ga:" + profile_id, start_date=start, end_date=end, max_results=100000, dimensions = dims,       metrics="ga:visits,ga:pageviews").execute()
    
    results=[]
    if limit=='Month':
        for row in data['rows']:
            newrow=[row[0]+'-'+row[1], row[2], row[3]]            
            results.append(newrow)
            
    elif limit=='Day':
        for row in data['rows']:            
            newrow=[row[0]+'-'+row[1] + '-' + row[2], row[3], row[4]]
            results.append(newrow)
    else:
        for row in data['rows']:            
            newrow=[row[0]+'-'+row[1], row[2], row[3]]
            results.append(newrow)          
    return results

@csrf_exempt
def ga_get_visits(start_date, end_date, limit):      
    
    service = initialize_service()
    try:   
        profile_id = get_first_profile_id(service)
        param = profile_id
        print profile_id   
        results = ga_get_visits_query(service, profile_id, start_date, end_date, limit)

	return results
	    
	    
    except TypeError, error:
        param=error 
    except HttpError, error:
        param=error
    except AccessTokenRefreshError:
        param=error

   
 
                
@csrf_exempt
def get_results(service, profile_id,checkedItems):
  # Use the Analytics Service Object to query the Core Reporting API
  print checkedItems
  return service.data().ga().get(
      ids="ga:" + profile_id,
      start_date="2013-01-01",
      end_date="2020-02-28",
      max_results=100000, 
      dimensions = "ga:pagePath, ga:medium",
      metrics="ga:pageviews",
      filters="ga:pagePath=~finished_signup;"+checkedItems).execute()
#      filters="ga:pagePath=~finished_signup").execute()
      
      
      
@csrf_exempt
def get_sourceliststring():
    service = initialize_service()
    try:
        profile_id = get_first_profile_id(service)       
        param = profile_id
        if profile_id:
	    results=get_sourcelist(service, profile_id)
	    sources = ""
	    for source in results:
	        sources = sources + "" +source[0] + ","
	    sources = sources[:-1]  
            return sources
            
    except TypeError, error:
        param=error 
    except HttpError, error:

        param=error
    except AccessTokenRefreshError:
        param=error
        
    
    c = Context({'googleanalytics_report': freelancerdemography_report,  'param': param})
    return HttpResponse(t.render(c))
      
@csrf_exempt
def get_sourcelist(service, profile_id):
  return service.data().ga().get(
      ids="ga:" + profile_id,
      start_date="2013-01-01",
      end_date="2020-02-28",
      max_results=100000, 
      dimensions = "ga:medium",
      metrics="ga:organicSearches").execute()['rows']
#      filters="ga:pagePath=~finished_signup").execute()      

#@permission_required('polls.can_vote')
@csrf_exempt        
def googleanalytics_report(request):
    
    t = loader.get_template('./reports/googleanalytics_report.html')
    service = initialize_service()
    try:
    # Step 2. Get the user's first profile ID.
        profile_id = get_first_profile_id(service)
        param = profile_id
        if profile_id:
	    results=get_sourcelist(service, profile_id)
	    sources = ""
	    for source in results:
	        sources = sources + "'" +source[0] + "',"
	    sources = "[" + sources[:-1]   + "]"   
            param = sources
           
           
      #print_results(results)

    except TypeError, error:
    # Handle errors in constructing a query.
        param=error 
     
    except HttpError, error:
    # Handle API errors.
        param=error

    except AccessTokenRefreshError:
    # Handle Auth errors.
        param=error
        
    
    c = Context({'googleanalytics_report': freelancerdemography_report,  'param': param})
    return HttpResponse(t.render(c))



@csrf_exempt        
def getcpcGroup(checkedItems):        
    service = initialize_service()
    try:   
        profile_id = get_first_profile_id(service)
        param = profile_id
        if profile_id:    
            results = get_results(service, profile_id,checkedItems)
            count=0
            userprofiles=""
            for userprofile in results['rows']:
                userprofiles = userprofiles + "'" + userprofile[0].replace("?just_finished_signup=True","").replace("/profile/","").replace("/","").replace("&edit=true","").lower() + "',"
                count=count+1
	    userprofiles= "(" + userprofiles[:-1] + ")"
	    return userprofiles
	    
    except TypeError, error:
        param=error 
    except HttpError, error:
        param=error
    except AccessTokenRefreshError:
        param=error
        
def getcpcGroupNewAndOld(checkedItems):      
    cpcresponse = getcpcGroup(checkedItems)
    sql1 = ("select id from users where lower(homepage) in " + cpcresponse)
    sql2 = ("select id from users where lower(cast(id as text)) in " + cpcresponse)
    
    result1 = customQuery(sql2,0)
    result2 = customQuery(sql1,2)
    
    result = result1 + result2
    #print result
    count=0
    userprofiles=""
    for userprofile in result:
        userprofiles = userprofiles + str(userprofile[0]) + ","
        count=count+1
    userprofiles= "(" + userprofiles[:-1] + ")"
    #print userprofiles
    return userprofiles
    
    
     


def get_first_profile_id(service):
  # Get a list of all Google Analytics accounts for this user
  accounts = service.management().accounts().list().execute()

  if accounts.get('items'):
    # Get the first Google Analytics account
    firstAccountId = accounts.get('items')[0].get('id')

    # Get a list of all the Web Properties for the first account
    webproperties = service.management().webproperties().list(accountId=firstAccountId).execute()

    if webproperties.get('items'):
      # Get the first Web Property ID
      firstWebpropertyId = webproperties.get('items')[0].get('id')

      # Get a list of all Views (Profiles) for the first Web Property of the first Account
      profiles = service.management().profiles().list(
          accountId=firstAccountId,
          webPropertyId=firstWebpropertyId).execute()

      if profiles.get('items'):
        # return the first View (Profile) ID
        return profiles.get('items')[0].get('id')

  return None
  
  
def detect(path):
    urllib.urlretrieve (path, "img.jpg") 
    img = cv2.imread("img.jpg")
    print img
    cascade = cv2.CascadeClassifier("/home/mahfouz/nabbeshreports/templates/haarcascade_frontalface_alt.xml")
    rects = cascade.detectMultiScale(img, 1.3, 4, cv2.cv.CV_HAAR_SCALE_IMAGE, (20,20)) 
    print rects
    return rects
