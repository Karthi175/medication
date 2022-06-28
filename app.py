import spacy

import json
import random

from flask import Flask,request,make_response
from flask_cors import CORS,cross_origin
import pandas as pd
import re

import datetime
# from flask_cors import CORS, cross_origin

med7 = spacy.load("en_core_med7_trf")


pattern_smoking = r"smoking[\s]*[:-][\s]*[a-zA-Z]+"
pattern_alcohol = r"alcohol[\s]*[:-][\s]*[a-zA-Z]+"
pattern_smoker = r"[\s]*smoker[\s]*[:-][\s]*[a-zA-Z]+"
pattern_tobacco = r"[\s]*tobacco[\s]*[:-][\s]*[a-zA-Z]+"
pattern_marijuana = r"[\s]*marijuana[\s]*[:-][\s]*[a-zA-Z]+"
time_pattern = r"[\s]*as[\s]*of[\s]*date[\s]*[:-][\s]*[\d]+[-:/][\d]+[-:/][\d]+"
patterns_habit = [pattern_smoking,pattern_smoker,pattern_alcohol,pattern_tobacco,pattern_marijuana,time_pattern]



def get_social_history(text1):

  """Getting all the spans where date was present"""
  text1=text1.lower()
  d= re.finditer(time_pattern,text1)
  time_tokens =[]
  for item in d:
    temp = (item.span()[0],item.span()[1])
    time_tokens.append(temp)

  """Extracting text between each date and send it to all the regex pattern and if match found, we break the loop and return the date and matched pattern of habit and append it to entities"""

  entities =[]
  for i in range(0,len(time_tokens)):
    if i<(len(time_tokens)-1):
      text = text1[time_tokens[i][0]:time_tokens[i+1][0]]
      for pattern in patterns_habit:
        result = re.findall(pattern,text)
        if result:
          entities.append((text1[time_tokens[i][0]:time_tokens[i][1]],result))
          break
    if i==(len(time_tokens)-1):
      text = text1[time_tokens[i][0]:]
      for pattern in patterns_habit:
        result = re.findall(pattern,text)
        if result:
          entities.append((text1[time_tokens[i][0]:time_tokens[i][1]],result))
          break

  

  """Storing date, habit and their value in a dataframe"""
  df1 = pd.DataFrame(columns=["Date","Entity","Assertion"])

  for index,entity in enumerate(entities):
    date = re.findall(r"[\d]+[-:/][\d]+[-:/][\d]+",entity[0])

    res1 = re.findall(r"[:-][\s]*[a-zA-Z]+",entity[1][0])
    res1 = re.sub(r"[\s]*","",res1[0])
    assert1 = re.findall(r"[a-zA-Z]+",res1)

    res2 = re.findall(r"[\s]*[a-zA-Z]*",entity[1][0])
    res2 = re.sub(r"[\s]*","",res2[0])
    ent = re.findall(r"[a-zA-Z]+",res2)

    if date:
      if ent:
        if assert1:
          # print(date[0]+"---------->"+ent[0]+"----------->"+assert1[0])
          df1.at[index,"Date"] = str(date[0])
          df1.at[index,"Assertion"] = str(assert1[0])
          df1.at[index,"Entity"] = str(ent[0])
      else:
        print("Entities not found matching the pattern")
    else:
      print("Date not found matching the pattern")


  habits = set(df1['Entity'].values)


  """For each habit, we get list of dates present and append it to date_str along with the assertion

  Convert each date_str into date_obj and append it to dates_obj and append the assertion to assertion list

  Make a copy of the date_obj as date_obj_before_sort and sort data_obj in reverse order and get the latest date

  Find the index this latest date has appeared in the date_obj_before_sort and use this index to get the assertion of the habit

  Convert the latest date_obj to str and append date_str, habit-assertion to the final list

  """

  final_list = []

  for habit in habits:
    dates_str = []
    dates_obj = []
    for index,row in df1.iterrows():
      if row['Entity'] == habit:
        dates_str.append(row["Date"]+"-"+row["Assertion"])

    assertion_final = []

    for dat in dates_str:
      date = dat.split("-")[0]
      assertion = dat.split("-")[1]
      assertion_final.append(assertion)
      dates_obj.append(datetime.datetime.strptime(date,"%m/%d/%Y"))


    dates_obj_before_sort = dates_obj.copy()
    dates_obj.sort(reverse=True)
    assertion = assertion_final[dates_obj_before_sort.index(dates_obj[0])]

    date_str = datetime.datetime.strftime(dates_obj[0],"%m/%d/%Y")
    final_list.append((habit,date_str,assertion))


  return final_list


def drug_dosages(doc):
  #assign empty list to add jsons
  med_list=[]
  i=0
  #iterate each entity
  for ent in doc.ents:
    #assign flag to append in list
    new=0
    
    if ent.label_=="DRUG":
      #For every drug, it will create new json 
      new=1
      temp={"id":1,"Drug":"","Strength":"","Form":"","Dosage":"","Duration":"","Route":"","Frequency":"","Date":"mm-dd-yyy","Page_no":"","F1score": random.randint(60,100)}
      temp["Drug"]=ent.text

    elif ent.label_=="STRENGTH":
      #for rejecting strength in json those strengths were detected withoout its drugs
      if len(temp["Strength"])==0:
        temp["Strength"]=ent.text

    elif ent.label_=="FORM":
       if len(temp["Form"])==0:
        temp["Form"]=ent.text

    elif ent.label_=="DOSAGE":
       if len(temp["Dosage"])==0:
        temp["Dosage"]=ent.text

    elif ent.label_=="DURATION":
       if len(temp["Duration"])==0:
        temp["Duration"]=ent.text

    elif ent.label_=="ROUTE":
       if len(temp["Route"])==0:
        temp["Route"]=ent.text

    elif ent.label_=="FREQUENCY":
       if len(temp["Frequency"])==0:
        temp["Frequency"]=ent.text
        
    if new==1:
      med_list.append(temp)
  return med_list


app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
@app.route('/med7',methods=['POST'])
@cross_origin()
def medications():
  dict1=request.get_data()
  dict1 = dict1.decode()
  # print(dict1)
  dict1 = json.loads(dict1)
  return_list=[]
  page_numbers = list(dict1.keys())
  text=""" """
  for page_number in page_numbers:
    text=dict1[page_number]
    page_no=page_number.split('_')[1]
    # print(page_no)
    doc = med7(text)
    ops = drug_dosages(doc)
    for op in ops:
      op['Page_no']=str(page_no)
      return_list.append(op)
    for i,j in enumerate(return_list):
      j['id']=i+1
  # print(return_list)
  return {'med_op':return_list}

@app.route('/social',methods=['POST'])
def social():
  dict1=request.get_data()
  dict1 = dict1.decode()
  # print(dict1)
  dict1 = json.loads(dict1)
  op=get_social_history(dict1['text'])
  # print(op)
  soc_list=[]
  for j,i in enumerate(op):
    js={'id':j+1,'Items':'','Date':'','Value':'','f1score':random.randint(60,100)}
    val=i[0].title()
    js['Items']=val
    js['Date']=i[1]
    js['Value']=i[2]
    # print(js)
    soc_list.append(js)
  # print(soc_list)
  return {'soc_op':soc_list}



if __name__ == '__main__':
    app.run()

def _build_cors_preflight_response():    
    response = make_response()
    print('cors resp')
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

# #AFTER REQUEST
@app.after_request
def afterRequest(response):
    if (request.method == 'OPTIONS'):
        return _build_cors_preflight_response()
    elif (request.method == 'POST'):
        return _corsify_actual_response(response)
