#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 21 13:46:02 2025

@author: zugmana2
"""
import pandas as pd
import json
import requests

import urllib.parse
def analyze_core_papers(doc):
    """Get the JSON data from the API response, extracts the main metadata fields, and saves them
     to the papers list

    :param doc: dict.
    :return: dict.
    """
    times_cited = 0
    for database in doc['dynamic_data']['citation_related']['tc_list']['silo_tc']:
        if database['coll_id'] == 'WOS':
            times_cited = database['local_count']
            break
    return {'UT': doc['UID'], 'times_cited': times_cited, 'tc_minus_sc': times_cited}



SEARCH_QUERY = 'AU=(Li Yang) and WC=(PSYCHIATRY or PSYCHOLOGY)'#'AU=(Li Yang)'#'AU=(Li Yang) and WC=(PSYCHIATRY or PSYCHOLOGY)'  # Enter the WoS search query here
APIKEY = "YOURKEYHERE"
HEADERS = {'X-APIKey': APIKEY}
initial_response = requests.get(
    f'https://wos-api.clarivate.com/api/wos?databaseId=WOS&usrQuery={urllib.parse.quote(SEARCH_QUERY)}&'
    f'count=0&firstRecord=1',
    headers=HEADERS,
    timeout=16, verify = False
)
data = initial_response.json()

total_records = data['QueryResult']['RecordsFound']

# Calculate the number of requests required.
requests_required = ((total_records - 1) // 100) + 1
# A list to store all required WoS document metadata
papers = []
papersdict = {}
# Calculate the number of requests required.
requests_required = ((total_records - 1) // 100) + 1
if requests_required > 1:
    print(f'API requests required to get all the author papers data: {requests_required}')

# Send requests to Web of Science Expanded API to get all the core papers
for i in range(requests_required):
    papersdict[i] = {}
    subsequent_response = requests.get(
        f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery={SEARCH_QUERY}&'
        f'count=100&firstRecord={i}01',
        headers=HEADERS,
        timeout=16, verify = False
    )
    papersdict[i]["query"] = f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery={SEARCH_QUERY}&count=100&firstRecord={i}01'
    data = subsequent_response.json()
    papersdict[i]["data"] = data
    for wos_record in data['Data']['Records']['records']['REC']:
        papers.append(analyze_core_papers(wos_record))
dataauthor = pd.DataFrame()
institutiondata = pd.DataFrame()
for data in  papersdict:
    for item in papersdict[data]["data"]['Data']['Records']['records']['REC']:
        UID = item["UID"]
        
        #for substaticitem in item["static_data"]:
        #    fm = substaticitem["fullrecord_metadata"]
        if not "contributors" in item["static_data"]:
            print("no author in this record")
        else:    
            authors =   item["static_data"]["contributors"]["contributor"]
           
            if item["static_data"]["contributors"]["count"] == 1:
                au = authors
                idx =  1    
                dataauthor = pd.concat([dataauthor,pd.DataFrame(au["name"],index=pd.MultiIndex.from_tuples(zip([UID],[idx]),names=("UID","order")))])
            elif item["static_data"]["contributors"]["count"] > 1:
                idx =1
                for au in authors:
                    idx = idx + 1    
                    dataauthor = pd.concat([dataauthor,pd.DataFrame(au["name"],index=pd.MultiIndex.from_tuples(zip([UID],[idx]),names=("UID","order")))])
        
        if  item["static_data"]["fullrecord_metadata"]["addresses"]["count"] > 1:
            addresses =   item["static_data"]["fullrecord_metadata"]["addresses"]["address_name"]
            for address in addresses:
                if "names" not in address:
                    continue
                names = address["names"]
                spec = address["address_spec"]
                if names["count"] == 1: 
                    n = names["name"]
                    dname = n
                    dname.pop("data-item-ids",None)
                    dname.pop("preferred_name",None)
                    dname["city"] = spec["city"]
                    dname["country"] = spec["country"]
                    dname["address"] = spec["full_address"]
                    institutiondata = pd.concat([institutiondata,pd.DataFrame(dname,index=pd.MultiIndex.from_tuples(zip([UID],[dname["seq_no"]]),names=("UID","order")))])
                     
                elif names["count"] > 1:
                    for n in names["name"]:
                        print(n)
                        dname = n
                        dname.pop("data-item-ids",None)
                        dname.pop("preferred_name",None)
                        dname["city"] = spec["city"]
                        dname["country"] = spec["country"]
                        dname["address"] = spec["full_address"]
                        institutiondata = pd.concat([institutiondata,pd.DataFrame(dname,index=pd.MultiIndex.from_tuples(zip([UID],[dname["seq_no"]]),names=("UID","order")))])
                                    
  
institutiondata.to_csv("~/Desktop/exampleAPIoutput.csv")
