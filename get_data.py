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
    start_date = parse(str(today - timedelta(days=6))).strftime("%m/%d/%Y")
    end_date = parse(str(today - timedelta(days=0))).strftime("%m/%d/%Y")
    date_range = parse(start_date).strftime("%m_%d_%Y") + '_to_' + \
            parse(end_date).strftime("%m_%d_%Y")

    #insert SQL query as string
    sql = f"""
        declare @start date = '{start_date}'
        --declare @end date = '{end_date}'
       
        
    ; with patients as
            (
            SELECT distinct tat.LAST_ASSIGNED_MD, tat.LAST_ASSIGNED_MD_ID
            , tat.FIRST_MD_SEEN, tat.FIRST_MD_SEEN_ID
            , tat.FIRST_RESIDENT_SEEN, tat.FIRST_RESIDENT_SEEN_ID
            , concat(tat.FIRST_RESIDENT_SEEN, ';', tat.FIRST_MD_SEEN,';',tat.LAST_ASSIGNED_MD) index_providers
            , left(tat.PT_ACUITY,1) as ESI 
            , tat.PATIENT_FIN index_fin, tat.PATIENT_NAME_FULL_FORMATTED pt_name, tat.PT_AGE pt_age
            , tat.REASON_FOR_VISIT index_rfv, tat2.REASON_FOR_VISIT return_rfv
            , tat2.PATIENT_FIN return_fin
            , DateDiff(hour,tat.[DISPO_DATE_TIME],tat2.[CHECKIN_DATE_TIME]) AS Bounceback_Hours
            , concat (tat.PT_DX1, ';', tat.pt_DX2, ';' , tat.pt_DX3) as index_diagnoses
            , concat (tat2.PT_DX1, ';', tat2.pt_DX2, ';' , tat2.pt_DX3)as return_diagnoses
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
            left outer join Providers_All_Years prov on tat.LAST_ASSIGNED_MD_ID = prov.Provider_ID
            left outer join Providers_All_Years prov2 on tat.FIRST_MD_SEEN_ID = prov2.Provider_ID
            left outer join Providers_All_Years prov3 on tat.FIRST_RESIDENT_SEEN_ID = prov3.Provider_ID
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
            )

    , first_note as
        (
        select pt_fin, result first_note_result from
                (select pt_fin, result, result_dt_tm, row_number() over (partition by pt_fin order by result_dt_tm) as RN
                from ED_NOTES_MASTER
                where note_type = 'Powernote ED'
                and pt_fin in 
                    (select index_fin from patients)
                ) a
            where a.rn = 1
        )

    , last_note as
        (
        select pt_fin, result last_note_result from
                (select pt_fin, result, row_number() over (partition by pt_fin order by result_dt_tm desc) as RN
                from ED_NOTES_MASTER
                where note_type = 'Powernote ED'
                and pt_fin in 
                    (select index_fin from patients)
            ) b
            where b.rn = 1
        )
        
    , return_note as
        (
            select pt_fin, result return_note from
                (select pt_fin, result, row_number() over (partition by pt_fin order by result_dt_tm desc) as RN
                from ED_NOTES_MASTER
                where note_type = 'Powernote ED'
                and pt_fin in 
                    (select return_fin from patients)
            ) c
            where c.rn = 1
        )

    select distinct patients.*, first_note.first_note_result, last_note.last_note_result
    , return_note.return_note
    , case 
        when role_first_resident = 'Physician Assistant' or role_first_resident = 'Nurse Practitioner' then 1
        when  role_first_md = 'Physician Assistant' or role_first_resident = 'Nurse Practitioner' then 1
        when  role_last_md = 'Physician Assistant' or role_first_resident = 'Nurse Practitioner' then 1
        ELSE 0
        END 'APP'
    , case 
        when role_first_resident = 'Fellow' then 1
        when  role_first_md = 'Fellow' then 1
        when  role_last_md = 'Fellow' then 1
        ELSE 0
        END 'Fellow'

    from patients
    left outer join first_note on patients.index_fin = first_note.pt_fin
    left outer join last_note on patients.index_fin = last_note.pt_fin
    left outer join return_note on patients.index_fin = return_note.pt_fin

    """
    return_visits = pd.read_sql(sql, conn)
    return_visits.drop_duplicates(subset='index_fin', keep='first', inplace=True)
    return_visits.columns = return_visits.columns.str.lower
    return_visits['provider'] = ''
    return_visits['provider_email'] = ''
    return_visits['provider_id'] = ''
    apps_fellows = return_visits[return_visits['app']==1 | (return_visits['Fellow'] == 1)]
    # set provider = first resident is APP is in the first resident column
    condition_first_res = apps_fellows['role_first_resident'].isin(['Physician Assistant', 'Nurse Practitioner', 'Fellow'])
    apps_fellows.loc[condition_first_res,['provider','provider_email', 'provider_id']
                     ] = apps_fellows.loc[condition_first_res
                                    ,['first_resident_seen','first_resident_email'
                                      ,'first_resident_seen_id']]
    # set provider = first MD if APP is in the first MD column
    condition_first_md = apps_fellows['role_first_md'].isin(['Physician Assistant', 'Nurse Practitioner'
                                                             , 'Fellow'])
    apps_fellows.loc[condition_first_md, ['provider','provider_email', 'provider_id']
                     ] = apps_fellows.loc[condition_first_md, ['first_md_seen', 'first_md_email'
                                                ,'first_md_seen_id']]
   
     # set provider = last MD if APP is in the last MD column
    condition_last_md = apps_fellows['role_last_md'].isin(['Physician Assistant', 'Nurse Practitioner', 'Fellow'])
    apps_fellows.loc[condition_last_md, ['provider','provider_email', 'provider_id']
                     ] = apps_fellows.loc[condition_last_md, ['last_assigned_md', 'last_assigned_md_email'
                                                ,'last_assigned_md_id']]
    # need to link to email addresses

    returns_with_admission = return_visits[return_visits['admit_visit2']==1]
    returns_with_admission['provider']=returns_with_admission['last_md_seen']
        
    # close all SQL connections

    for i in range(1, 200):
        conn = engine.connect()
        # some simple data operations
        conn.close()
        engine.dispose()       
    
    return return_visits, apps_fellows, returns_with_admission 

