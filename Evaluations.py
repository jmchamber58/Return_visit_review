"""
[] send email for fellows
[X] send email to residents (need to update the providers_all_years table)
"""

#%%
import os
import pandas as pd
from sql_server_conn import sql_server_alchemy_conn
from lastmonth import last_month
import pathlib
import email_jc as em
import datetime
from datetime import date, timedelta
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import win32com.client as win32
import numpy as np

conn, engine = sql_server_alchemy_conn()
today = date.today()
start_date = parse(str(today - timedelta(days=1))).strftime("%m/%d/%Y")
end_date = parse(str(today - timedelta(days=0))).strftime("%m/%d/%Y")
date_range = parse(start_date).strftime("%m_%d_%Y") + '_to_' + \
        parse(end_date).strftime("%m_%d_%Y")


#%%
sql = f"""
declare @start date = '{start_date}'
declare @end date = '{end_date}'
; with first_MD as
	(
	select patient_fin as pt_fin, FIRST_MD_SEEN, FIRST_MD_SEEN_ID, ProviderRole as Prov1Role, email as Prov1email
	from COVID_TAT tat
	inner join Providers_All_Years prov on FIRST_MD_SEEN_ID = prov.Provider_ID
	where format(CHECKIN_DATE_TIME,'MM/dd/yyyy') between @start and @end
	)

, first_res as
	(
	select patient_fin as pt_fin, FIRST_RESIDENT_SEEN, FIRST_RESIDENT_SEEN_ID, ProviderRole as Prov2Role, email as Prov2email
	from COVID_TAT tat
	inner join Providers_All_Years prov on FIRST_RESIDENT_SEEN_ID = prov.Provider_ID
	where format(CHECKIN_DATE_TIME,'MM/dd/yyyy') between @start and @end
	)

, last_MD as
	(
	select patient_fin as pt_fin, LAST_ASSIGNED_MD, LAST_ASSIGNED_MD_ID, ProviderRole as Prov3Role, email as Prov3email
	from COVID_TAT tat
	inner join Providers_All_Years prov on LAST_ASSIGNED_MD_ID = prov.Provider_ID
	where format(CHECKIN_DATE_TIME,'MM/dd/yyyy') = @start
	)

select distinct * from first_MD
inner join first_res on first_MD.pt_fin = first_res.pt_fin
inner join last_MD on first_MD.pt_fin = last_MD.pt_fin
"""
df = pd.read_sql(sql,conn)

#%%
df['Prov1email']=np.where((df['FIRST_MD_SEEN_ID']=='55416')&(df['Prov1email'].isna()),
    "HSHAUKAT2@childrensnational.org",df['Prov1email'])
df['Prov3email']=np.where((df['LAST_ASSIGNED_MD_ID']=='55416')&(df['Prov3email'].isna()),
    "HSHAUKAT2@childrensnational.org",df['Prov3email'])
#%%
df[['last_name', 'first_name_suffix']] = df['FIRST_RESIDENT_SEEN'].str.split(',', n=1, expand=True)
# Further split first_name_suffix to separate first name and remove suffix
df[['first_name', 'suffix']] = df['first_name_suffix'].str.strip().str.split(' ', n=1, expand=True)
# Drop the intermediate column and the suffix column if not needed
df = df.drop(columns=['first_name_suffix', 'suffix'])

df[['last_name_supervisor', 'first_name_suffix_supervisor']] = df['FIRST_MD_SEEN'].str.split(',', n=1, expand=True)
# Further split first_name_suffix to separate first name and remove suffix
df[['first_name_supervisor', 'suffix_supervisor']] = df['first_name_suffix_supervisor'].str.strip().str.split(' ', n=1, expand=True)
# Drop the intermediate column and the suffix column if not needed
df = df.drop(columns=['first_name_suffix_supervisor', 'suffix_supervisor'])

#%%
file_loc = pathlib.Path(os.environ['ONEDRIVE'],r"temp1/Evaluations")
file_name = f"{file_loc}/ED Evaluation Database.xlsx"
residents = pd.read_excel(file_name,sheet_name='Resident Information')

#%%
# Convert to lowercase
df['first_name_lower'] = df['first_name'].str.lower()
df['last_name_lower'] = df['last_name'].str.lower()
residents['first_name_lower'] = residents['First Name'].str.lower()
residents['first_name_lower'] = residents['first_name_lower'].str.rstrip()
residents['last_name_lower'] = residents['Last Name'].str.lower()
residents['last_name_lower'] = residents['last_name_lower'].str.rstrip()
residents['last_name_lower'] = residents['last_name_lower'].str.replace(',','')
residents['last_name_lower'] = residents['last_name_lower'].str.replace("'",'')
residents['last_name_lower'] = residents['last_name_lower'].str.replace("é",'e')
residents['last_name_lower'] = residents['last_name_lower'].str.replace("-",' ')
# Manual update names to match sql provider table
residents['last_name_lower'] = np.select(
    [residents['email']=="VBUSTAMANT@childrensnational.org",
    residents['email']=="HGERSCH@childrensnational.org",
    residents['email']=="janwadkarrohan@gmail.com",
    residents['email']=="bryan.knoedler12@gmail.com",
    residents['email']=="jakerquarl@gmail.com"],
    ['bustamante velez','gersch','rohan','bryan','jake'], 
    default=residents['last_name_lower']
)

residents['first_name_lower'] = np.select(
    [residents['email']=="LDESIRE@childrensnational.org",
    residents['email']=="JHJackso@childrensnational.org",
    residents['email']=="janwadkarrohan@gmail.com",
    residents['email']=="bryan.knoedler12@gmail.com",
    residents['email']=="seyitankolade@gmail.com",
    residents['email']=="jakerquarl@gmail.com",
    residents['email']=="TC.Schneider3@gmail.com",
    residents['email']=="marianjoy.spirnak@gmail.com",
    residents['email']=="rukhsyederas@gmail.com",
    residents['email']=="chriswalsh1993@gmail.com",],
    ['lynn','james','janwadkar','knoedler','oluwaoseyitan','quarles','trent','marian','shahrukh','chris'], 
    default=residents['first_name_lower']
)

# Merge
df_merged = df.merge(
    residents[['first_name_lower', 'last_name_lower', 'email',
               'Program','Training Year','Residency Type']],
    on=['first_name_lower', 'last_name_lower'],
    how='left'
)
#%%
# Update email field
col_list = ['Program','Training Year','Residency Type']
for col in col_list:
    df[col] = df_merged[col]
df['Prov2email_temp'] = df_merged['email']
df['Prov2email'] = np.where(df['Prov2email_temp'].isna(),df['Prov2email'], df['Prov2email_temp'])
df['Training Year'] = pd.to_numeric(df['Training Year'], errors='coerce').astype('Int64')


# Clean up
df.drop(columns=['first_name_lower', 'last_name_lower'], inplace=True)
#residents.drop(columns=['first_name_lower', 'last_name_lower'], inplace=True)

#%%
# Group by the two columns and count the occurrences
# this is for residents and APP
df_counts = df.groupby(['FIRST_MD_SEEN','Prov1Role','Prov1email',
                        'first_name_supervisor','last_name_supervisor',
                        'FIRST_RESIDENT_SEEN','first_name','last_name',
                        'Program','Training Year','Residency Type',
                        'Prov2Role', 'Prov2email']).size().reset_index(name=
                        'count')
df_counts = df_counts[df_counts['count'] >= 2]

#%%
"""
#remove suffix from first_name
--already did this on initial df
df_counts[['last_name', 'first_name_suffix']] = df_counts['FIRST_RESIDENT_SEEN'].str.split(',', n=1, expand=True)
# Further split first_name_suffix to separate first name and remove suffix
df_counts[['first_name', 'suffix']] = df_counts['first_name_suffix'].str.strip().str.split(' ', n=1, expand=True)
# Drop the intermediate column and the suffix column if not needed
df_counts = df_counts.drop(columns=['first_name_suffix', 'suffix'])

df_counts[['last_name_supervisor', 'first_name_suffix_supervisor']] = df_counts['FIRST_MD_SEEN'].str.split(',', n=1, expand=True)
# Further split first_name_suffix to separate first name and remove suffix
df_counts[['first_name_supervisor', 'suffix_supervisor']] = df_counts['first_name_suffix_supervisor'].str.strip().str.split(' ', n=1, expand=True)
# Drop the intermediate column and the suffix column if not needed
df_counts = df_counts.drop(columns=['first_name_suffix_supervisor', 'suffix_supervisor'])
"""

#%%
for _, row in df_counts.iterrows():
    first_name_supervisor = row['first_name_supervisor']
    last_name_supervisor = row['last_name_supervisor']
    recips = row['Prov1email']
    first_name = row['first_name']
    last_name = row['last_name']
    role = row['Prov2Role'].lower()
    year = row['Training Year']
    type = row['Residency Type']
    email_trainee = row['Prov2email']
    program = row['Program']
    if role == 'physician assistant':
        link = 'https://redcap.link/APPEval'
        program_text = " Physician Assistant at Children's National"
    elif role == 'resident':
        link = 'https://is.gd/edresident'
        program_text = f" resident in Year {year} of {type} at {program}"
    elif role == 'nurse practitioner':
        link = 'https://redcap.link/APPEval'
        program_text = " Nurse Practitioner at Children's National"
    supervisor_link = 'https://is.gd/edsupervisor' 
    count = row['count']
    subject="Please complete an evaluation"
    #recips = 'jchamber@childrensnational.org'#;hshaukat2@childrensnational.org '
    outlook = win32.Dispatch('outlook.application')
    mail = outlook.CreateItem(0)
    mail = outlook.CreateItem(0)
    mail.To = f"{recips}"
    mail.Subject = subject
    mail.HTMLbody = (f"""
                     <br>In the last 24 hours you worked with {first_name} {last_name}, 
                     who is a {program_text}. You evaluated {count} patients together. <br><br>
                     Please go to the following link to complete an evaluation <br><br>
            {link}
            """)
    mail.Send()
    subject="Please complete an evaluation"
    recips=row['Prov2email']
    #recips = 'jchamber@childrensnational.org'#;hshaukat2@childrensnational.org '
    outlook = win32.Dispatch('outlook.application')
    mail = outlook.CreateItem(0)
    mail = outlook.CreateItem(0)
    mail.To = f"{recips}"
    mail.Subject = subject
    mail.HTMLbody = (f"""
                     <br>In the last 24 hours you worked with {first_name_supervisor} {last_name_supervisor}
            and evaluated {count} patients together. <br><br>Please go to the following link 
            to complete an evaluation <br><br>
            {supervisor_link}
            """)
    mail.Send()
    # add email stuff here

#%%
# same process for fellows
df_fellows = df[(df['Prov1Role']=='Fellow') & (df['Prov3Role'] == 'Attending')]
df_fellow_counts = df_fellows.groupby(['FIRST_MD_SEEN','Prov1Role','Prov1email', 'LAST_ASSIGNED_MD', 'Prov3Role','Prov3email','first_name_supervisor', 'last_name_supervisor']).size().reset_index(name='count')
df_fellow_counts = df_fellow_counts[df_fellow_counts['count'] >= 2]
# %%
for _, row in df_fellow_counts.iterrows():
    recips = row['Prov3email']
    first_name = row['first_name_supervisor']
    last_name = row['last_name_supervisor']
    role = row['Prov1Role']
    link = 'https://cri-datacap.org/surveys/?s=8T7A9TTW4H8NWYPC' #fellow evaluations
    count = row['count']
    subject="Please complete an evaluation"
    #recips = 'jchamber@childrensnational.org'#;hshaukat2@childrensnational.org '
    outlook = win32.Dispatch('outlook.application')
    mail = outlook.CreateItem(0)
    mail = outlook.CreateItem(0)
    mail.To = f"{recips}"
    mail.Subject = subject
    mail.HTMLbody = (f"""<br>In the 24 hours you worked with {first_name} {last_name}
            and have evaluated {count} patients together. <br><br>Please go to the following link 
            to complete an evaluation <br><br>
            {link}
            """)
    mail.Send()

#%%
for i in range(1, 200):
    conn = engine.connect()
    # some simple data operations
    conn.close()
engine.dispose()

#%%
"""result_dict = {}
for _, row in df_counts.iterrows():
    # Use FIRST_MD_SEEN as the key
    key = row['Prov1email']
    # Combine first and last names into a list
    value = row['first_name'], row['last_name'], row['Prov2Role'], row['count']
    # Append to the dictionary
    if key not in result_dict:
        result_dict[key] = []
    result_dict[key].append(value)
"""

#%%
"""
for k,v in result_dict.items():
    recips = k
    first_name = v[0][0]
    last_name = v[0][1]
    role = v[0][2]
    count = v[0][3]
    # add email stuff here
"""
#%%
    

# %%
"""testing only
first_name = 'Andrea'
last_name = 'Birriel Sanchez'
count = 10
subject="Please complete an evaluation"
recips = 'jchamber@childrensnational.org'#;hshaukat2@childrensnational.org '
outlook = win32.Dispatch('outlook.application')
mail = outlook.CreateItem(0)
mail = outlook.CreateItem(0)
mail.To = f"{recips}"
mail.Subject = subject
mail.HTMLbody = 
    
mail.Send()
"""

# %%
