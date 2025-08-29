import get_data
import requests
import pandas as pd
import json


class Project(object):
    def __init__(self, url, token):
        self.token = token
        self.url = url

    def next_record(self):
        data = {'token': self.token,
                'content': 'generateNextRecordName'
                }
        r = requests.post(self.url, data=data)
        return r.text

    def write_record(self, record_to_write):
        data = {'token': self.token,
                'content': 'record',
                'action': 'import',
                'format': 'json',
                'type': 'flat',
                'overwriteBehavior': 'normal',
                'forceAutoNumber': 'false',
                'data': "[{}]".format(record_to_write),
                'returnContent': 'count',
                'returnFormat': 'json'
                }
        r = requests.post(self.url, data=data)
        print('HTTP Status: ' + str(r.status_code))
        print(r.text)

    def get_survey_link(self, record, instrument_name):
        data = {
            'token': self.token,
            'content': 'surveyLink',
            'format': 'json',
            'instrument': instrument_name,
            'event': '',
            'record': str(record),
            'returnFormat': 'json'
        }
        r = requests.post('https://cri-datacap.org/api/', data=data)
        return r.text

    def delete_record(self, records):
        data = {
            'token': self.token,
            'action': 'delete',
            'content': 'record',
        }
        records_dict = {
            f"records[{idx}]": record for idx, record in enumerate(records)}
        data.update(records_dict)
        r = requests.post('https://cri-datacap.org/api/', data=data)
        print('HTTP Status: ' + str(r.status_code))
        print(r.text)
"""
    def delete_all_records(self):
        data = {'token': self.token,
                'content': 'generateNextRecordName'
                }
        r = requests.post(self.url, data=data)
        next_record_int = int(r.text)
        user_spec = input(
            "Are you sure you want to delete all the records in this project? This action cannot be undone (y/n): ")
        if user_spec.lower() == "y":
            for i in range(next_record_int):
                data = {
                    'token': self.token,
                    'action': 'delete',
                    'content': 'record',
                }
                records_dict = {"records[0]": str(i)}
                data.update(records_dict)
                r = requests.post('https://cri-datacap.org/api/', data=data)
                print('HTTP Status: ' + str(r.status_code))
                print(r.text)
"""