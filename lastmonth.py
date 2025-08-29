# -*- coding: utf-8 -*-
"""
Created on Tue Jul  7 13:13:36 2020

@author: JCHAMBER
Returns start date, end date, and date range for last month
    Get the last day of last month by taking the first day of this month
    and subtracting 1 day. Set the day to 1 gives us the start of last month
"""

import datetime
import time
from dateutil.parser import parse


def last_month():
    """Returns start date, end date, and date range for last month"""
    now = time.localtime()
    end_date = datetime.date(now.tm_year, now.tm_mon, 1) - datetime.timedelta(1)
    start_date = end_date.replace(day=1)
    end_date = str(end_date)
    start_date = str(start_date)
    date_range = parse(str(start_date)).strftime("%m_%d_%Y") + '_to_' + \
        parse(str(end_date)).strftime("%m_%d_%Y")

    return start_date, end_date, date_range


