from get_data import query_data
df_fellows, df_residents, df_app, date_range = query_data()
from etl import fill_survey_resident, fill_survey_supervisor,fill_survey_fellow, fill_survey_app
import pandas as pd
from redcap_api import Project
pd.set_option('max_colwidth', 100000)
#queried_data = query_data()
df_list = [df_fellows, df_residents, df_app]
df_residents.to_excel(f"resident_output_{date_range}.xlsx",verbose=True) #outputs raw query data
df_app.to_excel(f"app_output_{date_range}.xlsx",verbose=True)
df_fellows.to_excel(f"fellow_output_{date_range}.xlsx",verbose=True)
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


