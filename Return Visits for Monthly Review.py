# -*- coding: utf-8 -*-
"""
Created on Thu Jul  2 15:50:29 2020

@author: jchamber
Pulls data on patients who return within one week and are admitted. Scheduled to run onthe 6th of each month.
Emails to Jim, who then distributes to providers who have return visits.
12/8/2023 added PA component for PAs seeing ESI3 patients independently

This was a starting point but now useing get_data.py
"""

# import pyodbc
from sql_server_conn import sql_server_conn
import win32com.client as win32
from lastmonth import last_month
import pandas as pd
import os
#import io

import datetime
from datetime import timedelta
from dateutil.parser import parse
#os.chdir(r"C:\temp")
#import xlsxwriter

conn = sql_server_conn()


file_path = r"J:\EMTC\DATA\ED Access Database\ED Department Files and Reports\Bouncebacks"
#file_path = r"C:\Users\jchamber\Downloads"
# os.chdir(file_path)
#start_date = '03/01/2021'
#end_date = '04/01/2021'
# set inclusion dates from 3/11/20 to yesterday. Define date range for inclusion in graphs and file names
"""
today = datetime.date.today()
start_date = parse(str(today - timedelta(days=36))).strftime("%m-%d-%Y")
end_date = parse(str(today - timedelta(days=6))).strftime("%m-%d-%Y")
#end_date = str(today)
date_range = parse(str(today - timedelta(days=36))).strftime("%m_%d_%Y") + '_to_' + \
    parse(str(today - timedelta(days=6))).strftime("%m_%d_%Y")
"""

start_date, end_date, date_range = last_month()

"""conn = pyodbc.connect('Driver={SQL Server};'
                      'Server=ENTSQL01LSNR;'
                      'Database=EMTCQIData;'
                      'Trusted_Connection=yes;')
"""


sql = """

SELECT tat.LAST_ASSIGNED_MD, tat.FIRST_MD_SEEN, tat.FIRST_RESIDENT_SEEN, left(tat.PT_ACUITY,1) as ESI, tat.PATIENT_FIN, tat.REASON_FOR_VISIT RFV1, tat2.REASON_FOR_VISIT RFV2
, DateDiff(hour,tat.[DISPO_DATE_TIME],tat2.[CHECKIN_DATE_TIME]) AS Bounceback_Hours, tat2.PT_DX1 
FROM ED_TAT_MASTER tat 
INNER JOIN ed_tat_master AS tat2 ON tat.PATIENT_MRN = tat2.PATIENT_MRN
WHERE tat.PATIENT_FIN<tat2.[PATIENT_FIN] AND tat2.REASON_FOR_VISIT Not Like 'Wound check' 
AND DateDiff(hour,tat.[DISPO_DATE_TIME],tat2.[CHECKIN_DATE_TIME])>8 
AND DateDiff(hour,tat.[DISPO_DATE_TIME],tat2.[CHECKIN_DATE_TIME])<168 AND tat2.PT_DX1 Not Like '%removal%' 
AND tat2.PT_DX1 Not Like '%wound check%' 
AND tat.PT_DISCH_DISPO Not Like '%IP' 
AND tat.PT_DISCH_DISPO Not Like '%admitted%' 
AND (tat2.PT_DISCH_DISPO Like '%IP' Or tat2.PT_DISCH_DISPO Like '%admitted%')
AND tat.LAST_ASSIGNED_MD is not null
AND tat.FIRST_MD_SEEN is not null
AND tat.checkin_date_time >= ? and tat.checkin_date_time < DATEADD(day,1,?) 
ORDER BY tat.LAST_ASSIGNED_MD, PATIENT_FIN, Bounceback_Hours

"""

sql_new = """

declare @start date = ?
declare @end date = ?

SELECT distinct tat.LAST_ASSIGNED_MD, tat.FIRST_MD_SEEN, tat.FIRST_RESIDENT_SEEN, left(tat.PT_ACUITY,1) as ESI 
, tat.PATIENT_FIN, tat.REASON_FOR_VISIT RFV1, tat2.REASON_FOR_VISIT RFV2
, DateDiff(hour,tat.[DISPO_DATE_TIME],tat2.[CHECKIN_DATE_TIME]) AS Bounceback_Hours, tat2.PT_DX1
, case when tat2.PT_DISCH_DISPO like 'admit%' then 1
	when tat2.PT_DISCH_DISPO like '%IP' then 1
	else 0
	end admit_visit2
, prov.ProviderRole as role

FROM ED_TAT_MASTER tat 
INNER JOIN ed_tat_master AS tat2 ON tat.PATIENT_MRN = tat2.PATIENT_MRN
left outer join Providers_All_Years prov on tat.LAST_ASSIGNED_MD = prov.Provider_Name
WHERE tat.PATIENT_FIN<tat2.[PATIENT_FIN] AND tat2.REASON_FOR_VISIT Not Like 'Wound check' 
AND DateDiff(hour,tat.[DISPO_DATE_TIME],tat2.[CHECKIN_DATE_TIME])>8 
AND DateDiff(hour,tat.[DISPO_DATE_TIME],tat2.[CHECKIN_DATE_TIME])<168 AND tat2.PT_DX1 Not Like '%removal%' 
AND tat2.PT_DX1 Not Like '%wound check%' 
AND tat.PT_DISCH_DISPO Not Like '%IP' 
AND tat.PT_DISCH_DISPO Not Like '%admitted%' 
--AND (tat2.PT_DISCH_DISPO Like '%IP' Or tat2.PT_DISCH_DISPO Like '%admitted%')
AND tat.LAST_ASSIGNED_MD is not null
AND tat.FIRST_MD_SEEN is not null
AND tat.checkin_date_time >= @start and tat.checkin_date_time < DATEADD(day,1,@end)
ORDER BY tat.LAST_ASSIGNED_MD, PATIENT_FIN, Bounceback_Hours

"""


returns = pd.read_sql(sql_new, conn, params=[start_date, end_date])
returns.drop_duplicates(subset='PATIENT_FIN', keep='first', inplace=True)


pa_returns = returns[returns['role']=='Physician Assistant']
pa_returns = pa_returns[pa_returns['FIRST_MD_SEEN']==pa_returns['LAST_ASSIGNED_MD']]
pa_returns = pa_returns[pa_returns['ESI']=='3']
pa_returns = pa_returns.drop(columns=['FIRST_MD_SEEN','FIRST_RESIDENT_SEEN'])
pa_returns_html = pa_returns.to_html(index=False)

pa_first_returns = returns[returns['FIRST_RESIDENT_SEEN'].str.contains(' PAC|PA-C',case=False,na=False)]
mapping = {'FIRST_RESIDENT_SEEN':'APP'}
pa_first_returns = pa_first_returns.rename(columns = mapping)
pa_first_returns_html = pa_first_returns.to_html(index=False)

fellow_returns = returns[returns['role']=='Fellow']
fellow_returns = fellow_returns.drop(columns=['FIRST_MD_SEEN','FIRST_RESIDENT_SEEN'])
fellow_returns_html = fellow_returns.to_html(index=False)

returns = returns.drop(columns=['FIRST_MD_SEEN','FIRST_RESIDENT_SEEN'])
returns_adm = returns[returns['admit_visit2']==1]
returns_adm = returns_adm.drop(columns = ['admit_visit2', 'role'])
returns_adm_html = returns_adm.to_html(index=False)

#returns_html = returns.to_html(index=False)

conn.close()

outlook = win32.Dispatch('outlook.application')  # Connects to your CNMC email
mail = outlook.CreateItem(0)
mail.To = "jchamber@cnmc.org;emtc_lip@childrensnational.org"
mail.Subject = 'New 7-Day Returns with Admission Data: Please review your charts'

# mail.Body = mail.Body = '''Below are our returns for last month resulting in admission within 7 days of an ED visit. Please review your patients.\n\n
#              {}'''.format(returns.to_string())#'Below are our returns for last month resulting in admission within 7 days of an ED visit. Please review your patients.'
mail.HTMLBody = f"""<p>
Below are returns within 7 days resulting in admission for {date_range}.
<br/>
<br/>
Please review your patients and reply to me with your categorization (could be more than one):
<br/>
<ul>
    <li>Progression of illness (appropriate medical care)</li>
    <li>Misdiagnosis or missed diagnosis</li>
    <li>Failure to obtain consultation when indicated</li>
    <li>Inability of family to obtain follow-up</li>
    <li>Failure of family to follow the treatment plan</li>
    <li>Data error</li>
    <li>Second visit unrelated to first</li>
</ul>
<br/>
Thanks 
<br/> 
Jim
<br/> 
</p>

{returns_adm_html}

"""
mail.Send()


outlook = win32.Dispatch('outlook.application')  # Connects to your CNMC email
mail = outlook.CreateItem(0)
mail.To = "jchamber@cnmc.org;cmoses@childrensnational.org"
mail.Subject = 'New 7-Day Returns Data: PA Data Level 3 ESI'
# mail.Body = mail.Body = '''Below are our returns for last month resulting in admission within 7 days of an ED visit. Please review your patients.\n\n
#              {}'''.format(returns.to_string())#'Below are our returns for last month resulting in admission within 7 days of an ED visit. Please review your patients.'
mail.HTMLBody = f"Below are PA ESI 3 patients with return within 7 days for {date_range}: \n\n{pa_returns_html}"
mail.Send()

outlook = win32.Dispatch('outlook.application')  # Connects to your CNMC email
mail = outlook.CreateItem(0)
mail.To = "jchamber@cnmc.org;cmoses@childrensnational.org"
mail.Subject = 'New 7-Day Returns Data: PA Data First Provider Seen Data'
# mail.Body = mail.Body = '''Below are our returns for last month resulting in admission within 7 days of an ED visit. Please review your patients.\n\n
#              {}'''.format(returns.to_string())#'Below are our returns for last month resulting in admission within 7 days of an ED visit. Please review your patients.'
mail.HTMLBody = f"Below are PA patients with return within 7 days for {date_range}: \n\n{pa_first_returns_html}"
mail.Send()

outlook = win32.Dispatch('outlook.application')  # Connects to your CNMC email
mail = outlook.CreateItem(0)
mail.To = "jchamber@cnmc.org"
mail.Subject = 'New 7-Day Returns Data: Please review your charts'

# mail.Body = mail.Body = '''Below are our returns for last month resulting in admission within 7 days of an ED visit. Please review your patients.\n\n
#              {}'''.format(returns.to_string())#'Below are our returns for last month resulting in admission within 7 days of an ED visit. Please review your patients.'
mail.HTMLBody = fellow_returns_html
mail.Send()

module_name = os.path.basename(__file__)
print(f"{module_name} is done running.")