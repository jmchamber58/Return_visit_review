#Import Dependencies

def query_data():
    """
    pulls data for returns within 7 days

    Arguments:
        None
    
    Returns:
        survey data to go to REDCap
    
    """
    import urllib
    from pandas.core.algorithms import unique
    from sql_server_conn import sql_server_alchemy_conn
    import pandas as pd
    from datetime import date, timedelta
    from dateutil.parser import parse
    from dateutil.relativedelta import relativedelta
    import time
    import numpy as np
    from dateutil.parser import parse
    import os
    import pathlib

    conn, engine = sql_server_alchemy_conn()
    today = date.today()
    start_date = parse(str(today - timedelta(days=4))).strftime("%m/%d/%Y")
    end_date = parse(str(today - timedelta(days=0))).strftime("%m/%d/%Y")
    date_range = parse(start_date).strftime("%m_%d_%Y") + '_to_' + \
            parse(end_date).strftime("%m_%d_%Y")

    #insert SQL query as string
    sql = f"""
        declare @start date = '{start_date}'
        --declare @end date = '{end_date}'

        SELECT distinct tat.LAST_ASSIGNED_MD, tat.LAST_ASSIGNED_MD_ID
        , tat.FIRST_MD_SEEN, tat.FIRST_MD_SEEN_ID
		, tat.FIRST_RESIDENT_SEEN, tat.FIRST_RESIDENT_SEEN_ID
        , concat(tat.FIRST_RESIDENT_SEEN, ';', tat.FIRST_MD_SEEN,';',tat.LAST_ASSIGNED_MD) index_providers
        , left(tat.PT_ACUITY,1) as ESI 
        , tat.PATIENT_FIN index_fin, tat.REASON_FOR_VISIT index_rfv, tat2.REASON_FOR_VISIT retunr_rfv
        , tat2.PATIENT_FIN return_fin
        , DateDiff(hour,tat.[DISPO_DATE_TIME],tat2.[CHECKIN_DATE_TIME]) AS Bounceback_Hours
        , concat (tat.PT_DX1, ';', tat.pt_DX2, ';' , tat.pt_DX3) as index_diagnoses
        , case when tat2.PT_DISCH_DISPO like 'admit%' then 1
            when tat2.PT_DISCH_DISPO like '%IP' then 1
            else 0
            end admit_visit2
        , prov.ProviderRole as role_last_md
        , prov2.ProviderRole as role_first_md
        , prov3.ProviderRole as role_first_resident
        , '' return_reasons
		, '' other_specify
		, prov.email as last_assigned_MD_email
		, prov2.email as first_assigned_MD_email
		, prov3.email as first_resident_email
	

        FROM ED_TAT_MASTER tat 
        INNER JOIN ed_tat_master AS tat2 ON tat.PATIENT_MRN = tat2.PATIENT_MRN
        left outer join Providers_All_Years prov on tat.LAST_ASSIGNED_MD = prov.Provider_Name
		left outer join Providers_All_Years prov2 on tat.FIRST_MD_SEEN = prov2.Provider_Name
		left outer join Providers_All_Years prov3 on tat.FIRST_RESIDENT_SEEN = prov3.Provider_Name
        WHERE tat.PATIENT_FIN<tat2.[PATIENT_FIN] AND tat2.REASON_FOR_VISIT Not Like 'Wound check' 
        AND DateDiff(hour,tat.[DISPO_DATE_TIME],tat2.[CHECKIN_DATE_TIME])>8 
        AND DateDiff(hour,tat.[DISPO_DATE_TIME],tat2.[CHECKIN_DATE_TIME])<168 AND tat2.PT_DX1 Not Like '%removal%' 
        AND tat2.PT_DX1 Not Like '%wound check%' 
        AND tat.PT_DISCH_DISPO Not Like '%IP' 
        AND tat.PT_DISCH_DISPO Not Like '%admitted%' 
        --AND (tat2.PT_DISCH_DISPO Like '%IP' Or tat2.PT_DISCH_DISPO Like '%admitted%')
        AND tat.LAST_ASSIGNED_MD is not null
        AND tat.FIRST_MD_SEEN is not null
        AND tat2.checkin_date_time >= @start --and tat.checkin_date_time < DATEADD(day,1,@end)
        --ORDER BY tat.LAST_ASSIGNED_MD, PATIENT_FIN, Bounceback_Hours

    """
    return_visits = pd.read_sql(sql, conn)
    return_visits.drop_duplicates(subset='PATIENT_FIN', keep='first', inplace=True)

    return return_visits 


"""




    # close all SQL connections
    for i in range(1, 200):
        conn = engine.connect()
        # some simple data operations
        conn.close()
        engine.dispose()

    #create first and last names for trainees
    df[['last_name', 'first_name_suffix']] = df['FIRST_RESIDENT_SEEN'].str.split(',', n=1, expand=True)
    # Further split first_name_suffix to separate first name and remove suffix
    df[['first_name', 'suffix']] = df['first_name_suffix'].str.strip().str.split(' ', n=1, expand=True)
    # Drop the intermediate column and the suffix column if not needed
    df = df.drop(columns=['first_name_suffix', 'suffix'])

    # create first and last names for supervisors
    df[['last_name_supervisor', 'first_name_suffix_supervisor']] = df['FIRST_MD_SEEN'].str.split(',', n=1, expand=True)
    # Further split first_name_suffix to separate first name and remove suffix
    df[['first_name_supervisor', 'suffix_supervisor']] = df['first_name_suffix_supervisor'].str.strip().str.split(' ', n=1, expand=True)
    # Drop the intermediate column and the suffix column if not needed
    df = df.drop(columns=['first_name_suffix_supervisor', 'suffix_supervisor'])

    file_loc = pathlib.Path(os.environ['ONEDRIVE'],r"temp1/Evaluations")
    file_name = f"{file_loc}/ED Evaluation Database.xlsx"
    residents = pd.read_excel(file_name,sheet_name='Resident Information')

    # Convert to lowercase
    df['first_name_lower'] = df['first_name'].str.lower()
    df['last_name_lower'] = df['last_name'].str.lower()
    residents['first_name_lower'] = residents['First Name'].str.lower()
    residents['last_name_lower'] = residents['Last Name'].str.lower()

    # Merge
    df_merged = df.merge(
        residents[['first_name_lower', 'last_name_lower', 'email',
                'Program','Training Year','Residency Type']],
        on=['first_name_lower', 'last_name_lower'],
        how='left'
    )

    # Update email field
    col_list = ['Program','Training Year','Residency Type']
    for col in col_list:
        df[col] = df_merged[col]
    df['Prov2email'] = df_merged['email']
    df['Training Year'] = pd.to_numeric(df['Training Year'], errors='coerce').astype('Int64')
    df['Training Year'] =  df['Training Year'].astype(str)
    df['program_type'] = df['Program'].fillna('') + ';' + df['Residency Type'].fillna('')

    # Clean up
    df.drop(columns=['first_name_lower', 'last_name_lower'], inplace=True)
    #residents.drop(columns=['first_name_lower', 'last_name_lower'], inplace=True)

    # Group by the two columns and count the occurrences
    # this is for residents and APP
    df_counts = df.groupby(['FIRST_MD_SEEN','Prov1Role','Prov1email',
                            'first_name_supervisor','last_name_supervisor',
                            'FIRST_RESIDENT_SEEN','first_name','last_name',
                            'Program','Training Year','Residency Type',
                            'Prov2Role', 'Prov2email','program_type','Prov3Role','Prov3email']).size().reset_index(name=
                            'count')
    df_counts = df_counts[df_counts['count'] >= 2]
    df_residents = df_counts[df_counts['Prov2Role']=='Resident']
    df_residents = df_residents[['FIRST_MD_SEEN', 'Prov1Role', 'Prov1email', 'first_name_supervisor',
        'last_name_supervisor', 'FIRST_RESIDENT_SEEN', 'first_name',
        'last_name', 'Program', 'Training Year', 'Residency Type', 'Prov2Role',
        'Prov2email', 'program_type', 'count']]
    df_fellows = df_counts[(df_counts['Prov1Role']=='Fellow') & (df_counts['Prov3Role'] == 'Attending')]
    df_fellows = df_fellows[['FIRST_MD_SEEN', 'Prov1Role', 'Prov1email', 'first_name_supervisor',
        'last_name_supervisor', 'Prov3email', 'count']]  
    df_fellows = df_fellows.rename(columns={'first_name_supervisor':'fellow_first_name','last_name_supervisor':'fellow_last_name'})                 
    df_app =  df_counts[(df_counts['Prov2Role']=='Physician Assistant') | (df_counts['Prov2Role']=='Nurse Practitioner')]
    df_app = df_app[['FIRST_MD_SEEN', 'Prov1Role', 'Prov1email', 'first_name_supervisor',
        'last_name_supervisor', 'FIRST_RESIDENT_SEEN', 'first_name',
        'last_name',  'Prov2Role', 'Prov2email', 'count']]
    df_app = df_app.rename(columns = {'FIRST_RESIDENT_SEEN':'FIRST_APP'})
    return df_fellows, df_residents, df_app, date_range

    """