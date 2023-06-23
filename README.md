# Youtube_Data_Harvesting_and_Warehousing

A Streamlit application that allows users to access and analyze data from multiple YouTube channel.
It takes channel ID as input and with the help of google api it fetches the channel's data and store it in a db in mongodb. In mongodb it is an unstructured format.
Then it migrates the data from mongodb to mysql in which it is in a structured format.

# 1.Tools USED

  Virtual code.
  
  Python 3.11.0 
  
  MySQL.
  
  MongoDB.
  
  Youtube API key.
  

# 2. Libraries Installed
 
  !pip install googleapiclient
  
  !pip install pymongo
  
  !pip install mysql-connector-python 
  
  !pip install sqlalchemy 
  
  !pip install pandas
  
  !pip install streamlit

# 3. ETL (Extract Transform Load) Process
 
  a) Extract data
  
    With the help of channel Id of a youtube channel and youtube API developer console we are extracting data.
    
  b) Process and Transform the data
  
    After the extraction process, take the required details from the extracted data and transformed to JSON Format.
    
  c) Load data
  
    Transformed data is first stored as JSON format in MongoDb and from it is migrated to MysQL AS structured data.
    
