#from settings import CHROMEDRIVER_PATH
import chromedriver_binary
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common import options
import os

import pandas as pd
import numpy as np
import time

# import streamlit
import streamlit as st


# -------------------------------- Page Design using Streamlit ----------------------------------------------
# Set page title
st.set_page_config(page_title='Survey Automation', page_icon=':tada', layout='wide')

# page Design
st.markdown("""
        <style>
               .block-container {
                    padding-top: 0rem;
                    padding-bottom: 0rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
        </style>        
        """, unsafe_allow_html=True)

st.markdown("<img src='https://1000logos.net/wp-content/uploads/2020/09/EMC-logo.png' alt='DELL EMC Logo' align='right' height='200'>", unsafe_allow_html=True)
st.markdown("<h2><font color='#007db8'>Welcome to Survey Evaluation Automation!</font></h2>", unsafe_allow_html=True)
# Initializing blank dataframe. Uploaded fill will get uploaded to this dataframe
data = pd.DataFrame()

# Using expander and under this providing the option to load CSV
with st.expander("Upload Class IDs"):
    file = st.file_uploader('File Upload')
    if file:
        data = pd.read_csv(file)
        st.dataframe(data)

# Progressbar for streamlit
progress_text = "Operation in progress. Please wait."
my_bar = st.progress(0, text=progress_text)

# Created table to store results in this format
final_table = pd.DataFrame()

# -------------------------------- Selenium Code for Automation ----------------------------------------------
#CHROMEDRIVER_PATH = 'chromedriver'

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")


# Load Required drivers and services
#service = Service(executable_path=CHROMEDRIVER_PATH)

# Set the path to the chromedriver binary
chromedriver_path = "/home/appuser/.wdm/drivers/chromedriver/linux64/111.0.5563/chromedriver"

# Change the permissions on the chromedriver binary
os.chmod(chromedriver_path, 775)
driver = webdriver.Chrome(chromedriver_path, options=chrome_options)




# Loop to fetch all the records 
for data_row in range (len(data)):

    # Initialize progress bar
    per = int(data_row/(len(data)) * 100)
    my_bar.progress(per, text=f'{per}% Percent Completed...')

    # Open weblink
    driver.get('https://dell.sabacloud.com/Saba/Web_spf/PRODTNT091/app/admin/learning/classes/manage')
    driver.maximize_window()

    # Wait for some time so that all component must get loaded ----- Changed wait time from 20 to 10 ------------
    driver.implicitly_wait(10)

    # Read iframe 
    iframe_element = driver.find_element(By.CSS_SELECTOR, 'iframe.ng-star-inserted')

    driver.switch_to.frame(iframe_element)

    # Fill class Id automatically
    class_id = driver.find_element(By.NAME, 'Catalog_query71331_var_part_no$kString$kEqual')

    # data that we extracting from dataframe is not String hence converting into a right form
    class_number = data['Class ID'].loc[data_row]
    class_number = f'000{class_number.astype(str)}'
    class_id.send_keys(class_number)

    # Click search button automatically
    search_button = driver.find_element(By.CLASS_NAME, 'sbWDKButton')
    search_button.click()

    # Get training StartDate and EndDate from main tab
    training_dates = driver.find_element(By.ID, 'idData_Catalog_result')
    dates_row = training_dates.find_elements(By.TAG_NAME, 'tr')
    dates_df = []

    for row in dates_row:
        try:
            col = row.find_elements(By.TAG_NAME,'td')[0]
            dates_df.append(col.text)
        except IndexError:
            pass
        continue

    temp = dates_df.copy()
    temp = temp[0]
    temp = temp.replace('Title\nVersion\nClass ID\nCourse ID\nDelivery\nLanguage\nStart Date\nEnd Date\nDomain\n','')

    dates_df = []
    for dates in temp.split():
        try:
            pd.to_datetime(dates)
            dates_df.append(dates)
        except: 
            pass 

    # Click on search link displayed automatically
    search_result = driver.find_element(By.CLASS_NAME, 'sbLinkTableDisplay')
    search_result.click()

    # Click on Activities Tab automatically
    try:
        act_tab = driver.find_element(By.CLASS_NAME, 'sbSectionText.ui_4')
        act_tab.click()
    except NoSuchElementException:
        act_tab = driver.find_element(By.CLASS_NAME, 'sbSectionText')
        act_tab.click()
    finally: # Using finally beucase noticed for class Id 0001605977 gives popup to click on Yes or No, so clicking on Yes from that popup else program will generate error
        try:
            driver.switch_to.alert.accept()
        except:
            pass
        
    # Wait for 10 seconds so that tool can extract information -------- Changed sleep time from 10 to 5 -------------------
    time.sleep(5)

    # ------------------------------------------ Now all the codes is to exteact trainer information ---------------------------------------------

    # Extract Rosources Table to find information about Trainer
    resources = driver.find_element(By.ID, 'id_offeringResources')
    res_row = resources.find_elements(By.TAG_NAME, 'tr')
    res_df = []

    for row in res_row:
        try:
            col = row.find_elements(By.TAG_NAME,'td')[0]
            res_df.append(col.text)
        except IndexError:
            pass
        continue
    
    res_temp = res_df.copy()
    res_temp = pd.DataFrame(res_temp)
    res_temp = res_temp.iloc[3]
    res_temp = res_temp.to_string()

    words = res_temp.split("\\n")
    words = ' '.join(words)
    words = words.replace("0    Purpose Resource Type Quantity Resource ID Resource Name Qualification Level Rate Instructor's Role Actions",'')
    words = words.replace('View/Edit Delete View Calendar','')

    # This is to store trainer badge Id and trainer name
    # Name is col12 because this requirment came late and till that time I was already done with all variables creation
    # hence do not want to change the codes again

    col12 = None 

    if 'Instructor  Person  0' in words:
        match = words.split('Instructor  Person  0')

        # Created count=1 beucase I observed 1st row is blank so do not want to capture that
        count = 1
        trainer = ''
        for var in match:
            if count == 1:
                count = count + 1
            else:
                trainer = trainer + var.partition(',')[0]
                col12 = trainer
        
    else:
        match = words.split('Instructor  Person  1')
        count = 1
        trainer = ''
        for var in match:
            if count == 1:
                count = count + 1
            else:
                trainer = trainer + var.partition(',')[0]
                col12 = trainer
    
    # ------------------------------------------ Now all the codes is to exteact Evaluation Table ---------------------------------------------

    # Extract Evaluation Table
    df=[]
    # Scroll page to the bottom
    bottom_of_the_page = driver.find_element(By.CLASS_NAME, 'sbDummy')
    driver.execute_script("arguments[0].scrollIntoView();",bottom_of_the_page)


    # Now Extract Evaluation Table
    results = driver.find_element(By.ID, 'id_EvaluationResultTable')
    rows = results.find_elements(By.TAG_NAME, 'tr')

    for row in rows:
        try:
            col = row.find_elements(By.TAG_NAME,'td')[0]
            df.append(col.text)
        except IndexError:
            pass
        continue

    temp = df.copy()
    temp = pd.DataFrame(temp)
    temp = temp.iloc[3].reset_index()
    temp.rename(columns = {3:'outcome'}, inplace = True)
    outcome = ' '.join(temp['outcome'])
    outcome = outcome.replace('Module\nEvaluation Status\nEvaluation Schedule\nExpiration Schedule\nVersion\nActive\nEvaluation for\nActions\n','')
    
    # Initializing blank row every time
    row = {}

    # Col1
    col1 = class_number
    print(col1) # Printing to understand till what class Ids it printed in case of error

    # Col2
    if 'Dell Technologies Post Event Evaluation' in outcome:
        col2 = 'Dell Technologies Post Event Evaluation'
    else:
        col2 = None

    # Col3
    if 'Dell Technologies Post Event Evaluation Published' in outcome:
        col3 = 'Published'
    else:
        col3 = None

    # Col4
    if 'Dell Technologies Post Event Evaluation Published Immediately on completion' in outcome:
        col4 = 'Immediately on completion'
    elif 'Dell Technologies Post Event Evaluation Published Immediately on class end date' in outcome:
        col4 = 'Immediately on class end date'
    else: 
        col4 = None

    # Col5
    if 'After 15 days of availability' in outcome:
        col5 = 'After 15 days of availability'
    elif 'No Expiration' in outcome:
        col5 = 'No Expiration'
    else:
        col5 = None

    # Col6
    if '6' in outcome:
        col6 = '6'
    else:
        col6 = None

    # Col7
    if 'Yes' in outcome:
        col7 = 'Yes'
    else:
        col7 = None

    # Col8
    if 'Learner' in outcome:
        col8 = 'Learner'
    else:
        col8 = None

    # Col9
    if 'No items found' in outcome:
        col9 = 'No Survey Found'
    else:
        col9 = 'Found'

    # This is to capture Course Title and Course ID
    main_header = driver.find_element(By.CLASS_NAME,'sbMainPageHeadingText')
    title = main_header.text
    title = title.replace('Virtual Classroom Details:','')
    title = title.split(',')
    col10 = title[0] # Capturing Course Title
    for i in title:
        if i.startswith('#'):
            col11 = i # Capturing Course ID
            break

    # Update ProgressBar
    per = int(data_row/(len(data)) * 100)
    my_bar.progress(per, text=f'{per}% Percent Completed...')    

    # Now entering all the values into right columns and this row I will save into a dataframe
    row = {'Class ID': col1, 'Start Date': dates_df[0], 'End Date':dates_df[1], 'Module': col2, 'Evaluation Status': col3, 'Evaluation Schedule':col4, 'Expiration Schedule':col5, 
        'Version':col6, 'Active':col7, 'Evaluation for':col8, 'Survey Status':col9, 'Course Title':col10, 'Course ID':col11, 
        'Badge ID - Trainer':col12}
    
    new_row = pd.DataFrame([row])
    final_table = pd.concat([final_table, new_row], axis=0, ignore_index=True)

# Display the results on Streamlit 
st.markdown('<h5>Results:</h5', unsafe_allow_html=True)
st.dataframe(final_table)



if len(final_table) != 0:
    # Also save results to .csv
    filename = f'Results_{time.strftime("%Y_%m_%d-%I_%M_%S_%p")}.csv'
    final_table.to_csv(filename)

    # Set status to 100%
    my_bar.progress(100, text='Completed')

    st.success(f'Results saved under filename : {filename}')


# Quit the application
driver.quit()

