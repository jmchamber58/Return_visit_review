#%%
from get_data import query_data
return_visits, apps_fellows, returns_with_admission = query_data()

#%%
# need to write etl for MD and APP
from etl import fill_survey
import pandas as pd
from redcap_api import Project
pd.set_option('max_colwidth', 100000)
#queried_data = query_data()

df_list = [apps_fellows, returns_with_admission]
for item in df_list:
    print(item)
    if len(item)==0:
        continue
    fill_survey(item)


# %%
