def fill_survey(dataframe):
    """
    takes data from dataframe and uses it to fill the REDCap survey

    Arguments:
        dataframe

    Returns:
        survey

    """
    
    from redcap_api import Project
    import json
    import pandas as pd
    #import config
    import numpy as np
    import time
    import win32com.client as win32
    import redcap_api
    from datetime import date, timedelta
    from dateutil.parser import parse
    from dateutil.relativedelta import relativedelta
    from dateutil.parser import parse
    today = date.today()
       
    with open('survey_dict.json', 'r') as file:
        blank_survey = json.load(file)

    data = dataframe
    blank_survey_df = pd.DataFrame(columns = blank_survey.keys()) #converts blank template survey into pandas datatype

    with open ('config.json','r') as config_file:
        config = json.load(config_file)
    redcap_database = Project(config['api_url'],config['api_key']) #you need to add API key and API URLs here, or use config
    first_record_id = int(redcap_database.next_record()) #gets the next record in the project to add data to, or use config

    #begin transformation
    survey = blank_survey_df

    #prep for transformations by fitting raw data into redcap survey slots

    survey['record_id'] = '' 
    # following line needs to change to account for other ptroviders
    survey['name'] = data['provider'].astype(str) 
    survey["provider_id"] = data ["provider_id"]
    survey['provider_email'] = data['provider_email']
    survey["index_providers"] = data ["index_providers"]
    survey["index_fin"] = data ["index_fin"]
    survey["pt_name"] = data ["pt_name"]
    survey["pt_age"] = data ["pt_age"]
    survey["index_date"] = data ["index_date"]
    survey["index_rfv"] = data ["index_rfv"]
    survey["index_diagnoses"] = data ["index_diagnoses"]
    survey["return_date"] = data ["return_date"]
    survey["return_rfv"] = data ["return_rfv"]
    survey["return_fin"] = data ["return_fin"]
    survey["return_diagnoses"] = data ["return_diagnoses"]
    survey["admit_return_visit"] = data["admit_visit2"]
    survey["first_note"] = data ["first_note_result"]
    survey["last_note"] = data ["last_note_result"]
    survey["return_note"] = data ["return_note_result"]
    survey['return_reasons___1'] = '' #reviewer multiple pick list
    survey['return_reasons___2'] = ''
    survey['return_reasons___3'] = ''
    survey['return_reasons___4'] = ''
    survey['return_reasons___5'] = ''
    survey['return_reasons___6'] = ''
    survey['return_reasons___7'] = ''
    survey['return_reasons___8'] = ''
    #survey["return_reasons"] = data["return_visits"]
    #survey["other_specify"] = data["other_specify"]
    survey["main_form_complete"] = ""




    # survey['supervisor'] = data['FIRST_MD_SEEN'].astype(str) --this will need to be mapped because it's a dropdown list

            #do race
    """
            conditions = [
            survey_duped['patient_race'].str.contains("Black", na=False),
            survey_duped['patient_race'].str.contains("Caucasian", na=False),
            survey_duped['patient_race'].str.contains("Asian", na=False),
            survey_duped['patient_race'].str.contains("Multiple", na=False),
            survey_duped['patient_race'].str.contains("Unknown", na=False),
            survey_duped['patient_race'].str.contains("Indian", na=False),
            survey_duped['patient_race'].str.contains("Hawaiian", na=False),
            survey_duped['patient_race'].str.contains("Other", na=False)
            ]

            choices = [1, 2, 3, 8, 6, 4, 5, 7]  # The numeric codes for race

            survey_duped['patient_race'] = np.select(conditions, choices, default=7).astype(str)
    """
    #do disposition


    # add redcap record_ids

    starting_value = first_record_id
    survey['record_id'] = (range(starting_value, starting_value + len(survey)))
    survey['record_id'] = survey['record_id'].astype(str)

    #convert all survey data elements into json objects and store those objects as lists
    json_objects = survey.apply(lambda x: x.to_json(), axis=1).tolist()

    #send data and get links
    links = []
    record_were_on = starting_value
    for record in json_objects:
        redcap_database.write_record(record)
        time.sleep(5)
        link = redcap_database.get_survey_link(record_were_on,"main_form")
        time.sleep(2)
        links.append(link)
        record_were_on+=1

    survey['survey_links'] = links

    #resident = data['first_name'] + ' ' + data['last_name']
    #doctor = data['last_name_supervisor']

    #process email assignments
    base_string = f"""<p>Dear Provider --</p>
        <p><br></p>Please review the chart of a patient who returned within 7 days. 
        Several of the fields are completed
        and the survey includes notes from the first and second visits.
        <p>.</span></p>
        """

# here I need to figure out how to parse the difference combinations of possible emails

    reviewers = survey['provider_email'].tolist() # don't want unique here because a supervisor might have more than one resident
    links = survey['survey_links'].to_list()
    
    
    #instantiate outlook
    outlook = win32.Dispatch('outlook.application')
    
    for reviewer in reviewers:
        mail = outlook.CreateItem(0)
        mail.To = reviewer
        #resident = survey.loc[survey['supervisor_email']==reviewer,'name']
        #enter email addresses to be CC'd below
        #mail.CC = "dberkowitz@childrensnational.org;jchamber@cnmc.org;nmccollum@childrensnational.org"
        mail.Subject = f"Please review a return visit"
        reviewer_links = survey.loc[survey['provider_email']==reviewer,'survey_links']##.to_list()
        body_string = f"{base_string}" # at {program}." this last part doesn't work because programs have been mapped to numbers
        for link in reviewer_links:
            body_string+=f"""\n<p> <a href='{link}'>{link}</a></p>"""
        #for i,link in zip(range(len(reviewer_links)),reviewer_links):
         #   body_string+="""\n<p>{0}. <a href="{1}">{1}</a></p>""".format(i+1,link)
        mail.HTMLbody =(body_string)
        mail.Send()
  
    return survey






#the following stuff is not needed


def fill_survey_last_md(dataframe):
    from redcap_api import Project
    import json
    import pandas as pd
    #import config
    import numpy as np
    import time
    import win32com.client as win32
    import redcap_api
    from datetime import date, timedelta
    from dateutil.parser import parse
    from dateutil.relativedelta import relativedelta
    from dateutil.parser import parse
    today = date.today()
        
    with open('survey.json', 'r') as file:
        blank_survey = json.load(file)

    data = dataframe
    blank_survey_df = pd.DataFrame(columns = blank_survey.keys()) #converts blank template survey into pandas datatype

    with open ('config.json','r') as config_file:
        config = json.load(config_file)
    redcap_database = Project(config['api_url'],config['api_key']) #you need to add API key and API URLs here, or use config
    first_record_id = int(redcap_database.next_record()) #gets the next record in the project to add data to, or use config

    #begin transformation
    survey = blank_survey_df

    #prep for transformations by fitting raw data into redcap survey slots

    survey['record_id'] = '' 

     


    #do disposition


    # add redcap record_ids

    starting_value = first_record_id
    survey['record_id'] = (range(starting_value, starting_value + len(survey)))
    survey['record_id'] = survey['record_id'].astype(str)

    #convert all survey data elements into json objects and store those objects as lists
    json_objects = survey.apply(lambda x: x.to_json(), axis=1).tolist()

    #send data and get links
    links = []
    record_were_on = starting_value
    for record in json_objects:
        redcap_database.write_record(record)
        time.sleep(5)
        link = redcap_database.get_survey_link(record_were_on,"supervisor_evaluation")
        time.sleep(2)
        links.append(link)
        record_were_on+=1

    survey['survey_links'] = links

    #resident = data['first_name'] + ' ' + data['last_name']
    #doctor = data['last_name_supervisor']

    #process email assignments
    base_string = f"""<p>Dear Doctor --</p>
        <p><br></p>Please complete an evaluation for an attending/fellow you worked with yesterday. Several of the fields are already completed.
        <p>.</span></p>
        """
    reviewers = survey['trainee_email'].unique().tolist()
    links = survey['survey_links'].to_list()
    
    #instantiate outlook
    outlook = win32.Dispatch('outlook.application')
    
    for reviewer in reviewers:
        mail = outlook.CreateItem(0)
        mail.To = reviewer
        #enter email addresses to be CC'd below
        mail.CC = "jchamber@cnmc.org"
        mail.Subject = 'Please complete an evaluation'
        reviewer_links = survey.loc[survey['trainee_email']==reviewer,'survey_links'].to_list()
        body_string = base_string
        for i,link in zip(range(len(reviewer_links)),reviewer_links):
            body_string+="""\n<p>{0}. <a href="{1}">{1}</a></p>""".format(i+1,link)
        mail.HTMLbody =(body_string)
        mail.Send()
    
    return survey


def fill_survey_fellow(dataframe):
    from redcap_api import Project
    import json
    import pandas as pd
    #import config
    import numpy as np
    import time
    import win32com.client as win32
    import redcap_api
    from datetime import date, timedelta
    from dateutil.parser import parse
    from dateutil.relativedelta import relativedelta
    from dateutil.parser import parse
    today = date.today()
        
    with open('survey.json', 'r') as file:
        blank_survey = json.load(file)

    data = dataframe
    blank_survey_df = pd.DataFrame(columns = blank_survey.keys()) #converts blank template survey into pandas datatype

    with open ('config.json','r') as config_file:
        config = json.load(config_file)
    redcap_database = Project(config['api_url'],config['api_key']) #you need to add API key and API URLs here, or use config
    first_record_id = int(redcap_database.next_record()) #gets the next record in the project to add data to, or use config

    #begin transformation
    survey = blank_survey_df

    #prep for transformations by fitting raw data into redcap survey slots

    survey['record_id'] = '' 

    #survey['fellow'] = data['fellow_first_name'] + ' ' + data['fellow_last_name']
    survey['supervisor_email'] = data['Prov1email']
    survey['supervisor_email'] = 'jchamber@cnmc.org'  #placeholder for testing

    survey['date'] = parse(str(today - timedelta(days=1))).strftime("%Y-%m-%d")

    #survey['supervisor'] = data[''first_name_supervisor'] + ' ' + data['last_name_supervisor]

    # add redcap record_ids

    starting_value = first_record_id
    survey['record_id'] = (range(starting_value, starting_value + len(survey)))
    survey['record_id'] = survey['record_id'].astype(str)

    #convert all survey data elements into json objects and store those objects as lists
    json_objects = survey.apply(lambda x: x.to_json(), axis=1).tolist()

    #send data and get links
    links = []
    record_were_on = starting_value
    for record in json_objects:
        redcap_database.write_record(record)
        time.sleep(5)
        link = redcap_database.get_survey_link(record_were_on,"fellow_feedback_on_the_fly")
        time.sleep(2)
        links.append(link)
        record_were_on+=1

    survey['survey_links'] = links

    #resident = data['first_name'] + ' ' + data['last_name']
    #doctor = data['last_name_supervisor']

    #process email assignments
    base_string = f"""<p>Dear Doctor --</p>
        <p><br></p>Please complete an evaluation for an attending/fellow you worked with yesterday. Several of the fields are already completed.
        <p>.</span></p>
        """
    reviewers = survey['supervisor_email'].unique().tolist()
    links = survey['survey_links'].to_list()
    
    #instantiate outlook
    outlook = win32.Dispatch('outlook.application')
    
    for reviewer in reviewers:
        mail = outlook.CreateItem(0)
        mail.To = reviewer
        #enter email addresses to be CC'd below
        mail.CC = "jchamber@cnmc.org"
        mail.Subject = 'Please complete an evaluation'
        reviewer_links = survey.loc[survey['supervisor_email']==reviewer,'survey_links'].to_list()
        body_string = base_string
        for i,link in zip(range(len(reviewer_links)),reviewer_links):
            body_string+="""\n<p>{0}. <a href="{1}">{1}</a></p>""".format(i+1,link)
        mail.HTMLbody =(body_string)
        mail.Send()
    
    return survey

def fill_survey_app(dataframe):
    from redcap_api import Project
    import json
    import pandas as pd
    #import config
    import numpy as np
    import time
    import win32com.client as win32
    import redcap_api
    from datetime import date, timedelta
    from dateutil.parser import parse
    from dateutil.relativedelta import relativedelta
    from dateutil.parser import parse
    today = date.today()
        
    with open('survey.json', 'r') as file:
        blank_survey = json.load(file)

    data = dataframe
    blank_survey_df = pd.DataFrame(columns = blank_survey.keys()) #converts blank template survey into pandas datatype

    with open ('config.json','r') as config_file:
        config = json.load(config_file)
    redcap_database = Project(config['api_url'],config['api_key']) #you need to add API key and API URLs here, or use config
    first_record_id = int(redcap_database.next_record()) #gets the next record in the project to add data to, or use config

    #begin transformation
    survey = blank_survey_df

    #prep for transformations by fitting raw data into redcap survey slots

    survey['record_id'] = '' 

    #survey['name'] = data['first_name'] + ' ' + data['last_name']
    #survey['name_2'] = data['first_name_supervisor'] + ' ' + data['last_name_supervisor']
    survey['supervisor_email'] = data['Prov1email']
    #survey['supervisor_email'] = 'jchamber@cnmc.org'  #placeholder for testing

    survey['date'] = parse(str(today - timedelta(days=1))).strftime("%Y-%m-%d")

    #survey['supervisor'] = data[''first_name_supervisor'] + ' ' + data['last_name_supervisor]

    # add redcap record_ids

    starting_value = first_record_id
    survey['record_id'] = (range(starting_value, starting_value + len(survey)))
    survey['record_id'] = survey['record_id'].astype(str)

    #convert all survey data elements into json objects and store those objects as lists
    json_objects = survey.apply(lambda x: x.to_json(), axis=1).tolist()

    #send data and get links
    links = []
    record_were_on = starting_value
    for record in json_objects:
        redcap_database.write_record(record)
        time.sleep(5)
        link = redcap_database.get_survey_link(record_were_on,"physician_assistant_independent_practice_survey")
        time.sleep(2)
        links.append(link)
        record_were_on+=1

    survey['survey_links'] = links

    #resident = data['first_name'] + ' ' + data['last_name']
    #doctor = data['last_name_supervisor']

    #process email assignments
    base_string = f"""<p>Dear Doctor --</p>
        <p><br></p>Please complete an evaluation for an advanced practice provider you worked with yesterday. Several of the fields are already completed.
        <p>.</span></p>
        """
    reviewers = survey['supervisor_email'].unique().tolist()
    links = survey['survey_links'].to_list()
    
    #instantiate outlook
    outlook = win32.Dispatch('outlook.application')
    
    for reviewer in reviewers:
        mail = outlook.CreateItem(0)
        mail.To = reviewer
        #enter email addresses to be CC'd below
        mail.CC = "jchamber@cnmc.org"
        mail.Subject = 'Please complete an evaluation'
        reviewer_links = survey.loc[survey['supervisor_email']==reviewer,'survey_links'].to_list()
        body_string = base_string
        for i,link in zip(range(len(reviewer_links)),reviewer_links):
            body_string+="""\n<p>{0}. <a href="{1}">{1}</a></p>""".format(i+1,link)
        mail.HTMLbody =(body_string)
        mail.Send()
    
    return survey

