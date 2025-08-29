# -*- coding: utf-8 -*-
"""
Created on Fri Jul 16 08:31:51 2021

@author: JCHAMBER
"""

def sql_server_conn():
       """This provides connection to SQL Server using pyodbc with ODBC Driver 17"""
       
       #conn = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};'
        #                     'Server=tcp:ENTSQL01LSNR;'
         #                    'Database=EMTCQIData;'
          #                   'Trusted_Connection=yes;')
       #return conn

       import pyodbc
       conn = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};'
                      'Server=tcp:ENTSQL01LSNR;'
                      'Database=EMTCQIData;'
                      'Trusted_Connection=yes;'
                      'MultiSubnetFailover=Yes;'
                      'Encrypt=yes;'
                      'TrustServerCertificate=yes')
       return conn

def sql_server_alchemy_conn():
       #This provides connection to SQL Server using sqlalchemy
       import sqlalchemy as sa
       import urllib
       from sqlalchemy import create_engine
       connection= urllib.parse.quote_plus('Driver={ODBC Driver 17 for SQL Server};'
                      'Server=tcp:ENTSQL01LSNR;'
                      'Database=EMTCQIData;'
                      'Trusted_Connection=yes;'
                      'MultiSubnetFailover=Yes;'
                      'Encrypt=yes;'
                      'TrustServerCertificate=yes')
       
       
       engine = sa.create_engine('mssql+pyodbc:///?odbc_connect={}'.format(connection))
       conn = engine.connect().execution_options(stream_results=True)
       return conn, engine
