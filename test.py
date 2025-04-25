#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 23 15:36:16 2025

@author: zugmana2
"""
#from habanero import cn,Crossref,counts
from pathlib import Path
import requests
import urllib.parse
import pandas as pd
import time
#import json

def writeris(ristext,path):
    if not Path(path).exists():
        with open(path,'w+') as file:
            file.write(ristext)
    else :
        with open(path,'a') as file:
            file.write('\n')
            file.write(ristext)
def normalize_string(s):
    return s.lower().split()

def common_word_count(str1, str2):
    words1 = set(normalize_string(str1))
    words2 = set(normalize_string(str2))
    return len(words1 & words2)

def find_best_match(dicts, query_string):
    max_common_words = 0
    best_match = None
    
    for d in dicts:
        if 'title' in d:
            common_words = common_word_count(query_string, d['title'][0])
            if common_words > max_common_words:
                max_common_words = common_words
                best_match = d
                
    return best_match
# ris = cn.content_negotiation(ids = '10.1126/science.169.3946.635',format='ris')
# test_path = Path("/Users/zugmana2/Desktop/test.ris")
# writeris(ris, test_path)
# ris = cn.content_negotiation(ids = '10.31887/DCNS.2015.17.3/macrocq',format='ris')
# test_path = Path("/Users/zugmana2/Desktop/test.ris")
# writeris(ris, test_path)

# cr = Crossref()
# x = cr.works(query =  "AUTHOR='Wittchen HU'")
# title = urllib.parse.quote("Prevalence, severity, and comorbidity of twelve-month DSM-IV disorders in the National Comorbidity Survey Replication (NCS-R)")
# author = urllib.parse.quote("Kandler")
# x = requests.get(f'https://api.crossref.org/works?query.title={title}&query.author={author}/application/x-research-info-systems',verify = False)

#This is to get it in ris
#a= {"Accept" : "application/x-research-info-systems" }
#x = httpx.get('https://doi.org/10.31887/DCNS.2015.17.3/macrocq',verify = False,
#                 headers=a,  follow_redirects=True)

refs = pd.read_csv('~/Documents/dois_corey.csv',sep='\t')
refs["OK"] = ""
ris_path = Path("~/Documents/test.ris")
a= {"Accept" : "application/x-research-info-systems" }
for idx,doi in enumerate(refs["VALUE!"]):
    print(f"https://doi.org/{doi}")
    x = requests.get(f'https://doi.org/{doi}',verify = False,
                     headers=a,  allow_redirects=True)
    if x.status_code == 200:
       writeris(x.text, ris_path)
       refs.loc[idx,"OK"] = "OK"
    else:
        print("DOI not found")
        authordict = {}
        #Look for author publication
        author = refs.loc[idx,"References"].split(" ")[1]
        author = urllib.parse.quote(author)
        rows = 201
        counter = 1
        while rows >= 200:
            if counter ==1:
                x = requests.get(f"https://api.crossref.org/works?query.author={author}&cursor=*&rows=200", verify=False)
                d = x.json()
                authordict["items"] = d["message"]["items"]
                counter = 2
                nextcursor = d["message"]["next-cursor"]
                rows = len(d["message"]["items"])
            else:
                x = requests.get(f"https://api.crossref.org/works?query.author={author}&cursor={nextcursor}&rows=200", verify=False)
                d = x.json()
                authordict["items"] += d["message"]["items"]
                counter = 2
                nextcursor = d["message"]["next-cursor"]
                rows = len(d["message"]["items"])
                time.sleep(2) # sleep two seconds not to break the API
        title = refs.loc[idx,"References"].split(".")[2]
        probablemathc = find_best_match(authordict["items"],title)
        updateddoi = probablemathc["DOI"]
        x = requests.get(f'https://doi.org/{doi}',verify = False,
                         headers=a,  allow_redirects=True)
        if x.status_code == 200:
           writeris(x.text, ris_path)
           refs.loc[idx,"OK"] = "OK"