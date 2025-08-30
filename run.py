#%%
from get_data import query_data
return_visits, apps, returns_with_admission, fellows = query_data()

#%%
# need to write etl for MD and APP
from etl import fill_survey_last_md, fill_survey_app, fill_survey_fellow
import pandas as pd
from redcap_api import Project
pd.set_option('max_colwidth', 100000)
#queried_data = query_data()


df_list = [apps, returns_with_admission, fellows]
for item in df_list:
    print(item)
    if len(item)==0:
        continue
    
    if  'FIRST_RESIDENT_SEEN' in item.columns:
        final_resident_data = fill_survey_resident(item)
        final_supervisor_data = fill_survey_supervisor(item)
        final_resident_data.to_excel(f"final_resident_data_{date_range}.xlsx", verbose = True)
        final_supervisor_data.to_excel(f"final_supervisor_data_{date_range}.xlsx", verbose = True)
    elif 'Prov3email' in item.columns:
        # open fellow evals
        final_fellow_data = fill_survey_fellow(item)
        final_fellow_data.to_excel(f"final_fellow_data_{date_range}.xlsx", verbose = True)
    elif 'FIRST_APP' in item.columns:
        # do APP evals
        final_app_data = fill_survey_app(item)
        final_app_data.to_excel(f"final_app_data_{date_range}.xlsx", verbose = True)


