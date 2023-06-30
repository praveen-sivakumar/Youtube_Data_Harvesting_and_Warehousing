#------------------------------------------Importing Required Libraries---------------------------------------------
from googleapiclient.discovery import build

import re
import pymongo
import mysql.connector

import sqlalchemy
from sqlalchemy import create_engine

import streamlit as st
from streamlit_option_menu import option_menu

import pandas as pd
import plotly.express as px  
#------------------------------------------Page Configuration Setup-------------------------------------------------

st.set_page_config(page_title="YouTube",
                   layout="wide",
                   initial_sidebar_state='auto',
                   menu_items={'About':'Application developed by Praveen Sivakumar'}
                   )



#-------------------------------------------Creating Navigation bar-------------------------------------------------

selected = option_menu(
        menu_title = None,
        options=["Home","Data Processing","Data Analysis","About"],
        icons=["house-fill","database-fill",'graph-up-arrow',"exclamation-lg"],
        default_index=0,
        orientation="horizontal",
        styles={
                "container": {"background-color": "#000000"},
                "icon": {"color": "white", "font-size": "25px"},
                "nav-link": {"text-align": "centre","--hover-color": "white", "color" : "white"},
                "nav-link-selected": {"background-color": "red"}
        }
    )

st.header(":red[YouTube Data Harvesting and Warehousing using SQL, MongoDB and Streamlit]")

#------------------------------------------------------Home---------------------------------------------------------
if selected == 'Home':
    st.subheader('Home')
   
    st.markdown(':red[**_YouTube Data Harvesting and Warehousing_**] is a Streamlit application that allows users to access and analyze data from multiple YouTube channels.')

    st.write('''**It involves building a simple UI with Streamlit, retrieving data from the YouTube API, storing it in a MongoDB, migrating it to a SQL data warehouse, querying the data warehouse with SQL, and displaying the data in the Streamlit app.**''')

    st.write(''':red[**_The application has the following features,_**]\n
    1. Ability to input a YouTube channel ID and retrieve all the relevant data using Google API.\n
    2. Option to store the data in a MongoDB database.\n
    3. Option to select a channel name and migrate its data from the MongoDB to a SQL database as tables.\n
    4. Ability to search and retrieve data from the SQL database using different search options to get channel details.''')
    
    st.subheader('_Process_')

    st.markdown('**:red[Step 1] :**  We fetch the details of a youTube channel with the help of a Google API and channel ID.')

    st.markdown('**:red[Step 2] :**  We process the data and store in MongoDB as JSON format (unstructured format).')

    st.markdown('**:red[Step 3] :**  We fetch the data from MongoDB, process it and store it in a MySql database (structured format).')

    st.markdown('**:red[Step 4] :**  We create a web application using Streamlit library of Python')

    st.markdown('**:red[Step 5] :**  In the application we provide data visualization option to the user depending on the questions they choose')

    st.markdown('**:red[Step 6] :**  Data Visualization is been done with the help of python libraries like plotly and pandas')

    st.subheader('_Outcome_')

    st.markdown('''Users can fetch the details of a YouTube channel by just entering the channel's ID and store it in both MongoDB and Sql. They can also analyse the data with 10 provided questions.''')
#------------------------------------------------------Data Processing----------------------------------------------
if selected == 'Data Processing':

    #--------------------------------------------------Data Collection-----------------------------------------------
    st.subheader('Data Collection')
    channel_id = st.text_input(':red[**_Enter the channel_id :_**]')
    Fetch_Data = st.button('**Fetch and Store**')

    if Fetch_Data == True:
        # Youtube API
        api_service_name = 'youtube'
        api_version = 'v3'
        api_key = 'AIzaSyBU8lTY3AZH6iroO8Vb0NNavSLCE5AInBg'
        youtube = build(api_service_name,api_version,developerKey=api_key)

        # Fetching channel data
        def get_channel_data(youtube,channel_id):
            channel_request = youtube.channels().list(
                part = 'snippet,statistics,contentDetails',
                id = channel_id)
            channel_response = channel_request.execute()
                    
            if 'items' not in channel_response:
                st.write(f"Invalid channel id: {channel_id}")
                st.error("Enter the **channel_id**")
                return None
                    
            return channel_response

        channel_data = get_channel_data(youtube,channel_id)

        channel_name = channel_data['items'][0]['snippet']['title']
        channel_video_count = channel_data['items'][0]['statistics']['videoCount']
        channel_subscriber_count = channel_data['items'][0]['statistics']['subscriberCount']
        channel_view_count = channel_data['items'][0]['statistics']['viewCount']
        channel_description = channel_data['items'][0]['snippet']['description']
        channel_playlist_id = channel_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        # Channel_data in dictionary

        channel = {
            "Channel_Details": {
                "Channel_Name": channel_name,
                "Channel_Id": channel_id,
                "Video_Count": channel_video_count,
                "Subscriber_Count": channel_subscriber_count,
                "Channel_Views": channel_view_count,
                "Channel_Description": channel_description,
                "Playlist_Id": channel_playlist_id
            }
        }
        
        # Fetching video IDs from channel playlist
        def get_video_ids(youtube, channel_playlist_id): 
            video_id = []
            next_page_token = None
            while True:
                # Get playlist items
                request = youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId=channel_playlist_id,
                    maxResults=50,
                    pageToken=next_page_token)
                response = request.execute()

                # Get video IDs
                for item in response['items']:
                    video_id.append(item['contentDetails']['videoId'])

                # Check if there are more pages
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

            return video_id

        video_ids = get_video_ids(youtube, channel_playlist_id)

        # Retrieving video data
        def get_video_data(youtube, video_ids):
            video_data = []
            for video_id in video_ids:
                try:
                    request = youtube.videos().list(
                    part='snippet, statistics, contentDetails',
                    id=video_id)
                    response = request.execute()

                    video = response['items'][0]
                    
                    # Comments if available
                    try:
                     video['comment_threads'] = get_video_comments(youtube, video_id, max_comments=2)
                    except:
                        video['comment_threads'] = None

                    # Duration format transformation (Duration format transformation function call)
                    duration = video.get('contentDetails', {}).get('duration', 'Not Available')
                    if duration != 'Not Available':
                        duration = convert_duration(duration)
                    video['contentDetails']['duration'] = duration        
                                
                    video_data.append(video)
                    
                except:
                    st.write('You have exceeded your YouTube API quota. Please try again tomorrow.')

            return video_data

        # Retrieving video comments
        def get_video_comments(youtube, video_id, max_comments):   
            request = youtube.commentThreads().list(
                part='snippet',
                maxResults=max_comments,
                textFormat="plainText",
                videoId=video_id)
            response = request.execute()
            
            return response

        # Define a function to convert duration
        def convert_duration(duration):
            regex = r'PT(\d+H)?(\d+M)?(\d+S)?'
            match = re.match(regex, duration)
            if not match:
                return '00:00:00'
            hours, minutes, seconds = match.groups()
            hours = int(hours[:-1]) if hours else 0
            minutes = int(minutes[:-1]) if minutes else 0
            seconds = int(seconds[:-1]) if seconds else 0
            total_seconds = hours * 3600 + minutes * 60 + seconds
            return '{:02d}:{:02d}:{:02d}'.format(int(total_seconds / 3600), int((total_seconds % 3600) / 60), int(total_seconds % 60))

        video_data = get_video_data(youtube, video_ids)


        # Video details
        videos = {}
        for i, video in enumerate (video_data):
            video_id = video['id']
            video_name = video['snippet']['title']
            video_description = video['snippet']['description']
            tags = video['snippet'].get('tags', [])
            published_at = video['snippet']['publishedAt']
            view_count = video['statistics']['viewCount']
            like_count = video['statistics'].get('likeCount', 0)
            dislike_count = video['statistics'].get('dislikeCount', 0)
            favorite_count = video['statistics'].get('favoriteCount', 0)
            comment_count = video['statistics'].get('commentCount', 0)
            duration = video.get('contentDetails', {}).get('duration', 'Not Available')
            thumbnail = video['snippet']['thumbnails']['high']['url']
            caption_status = video.get('contentDetails', {}).get('caption', 'Not Available')
            comments = 'Unavailable'

            # Handle case where comments are enabled
            if video['comment_threads'] is not None:
                comments = {}
                for index, comment_thread in enumerate(video['comment_threads']['items']):
                    comment = comment_thread['snippet']['topLevelComment']['snippet']
                    comment_id = comment_thread['id']
                    comment_text = comment['textDisplay']
                    comment_author = comment['authorDisplayName']
                    comment_published_at = comment['publishedAt']
                    comments[f"Comment_Id_{index + 1}"] = {
                        'Comment_Id': comment_id,
                        'Comment_Text': comment_text,
                        'Comment_Author': comment_author,
                        'Comment_PublishedAt': comment_published_at
                    }
                    
            # Video data into dictionary        
            videos[f"Video_Id_{i + 1}"] = {
                'Video_Id': video_id,
                'Video_Name': video_name,
                'Video_Description': video_description,
                'Tags': tags,
                'PublishedAt': published_at,
                'View_Count': view_count,
                'Like_Count': like_count,
                'Dislike_Count': dislike_count,
                'Favorite_Count': favorite_count,
                'Comment_Count': comment_count,
                'Duration': duration,
                'Thumbnail': thumbnail,
                'Caption_Status': caption_status,
                'Comments': comments
            }

        # Channel data and videos data to a dict 
        final_output = {**channel, **videos}

        # -----------------------------------    /   MongoDB connection and store the collected data   /    ---------------------------------- #

        client = pymongo.MongoClient('mongodb+srv://praveensivakumar:1111@cluster0.jxaowcs.mongodb.net/')
        mydb = client['Youtube_DB']
        collection = mydb['Youtube_data']
        final_output_data = {
            'Channel_Name': channel_name,
            "Channel_data":final_output
            }
        upload = collection.replace_one({'_id': channel_id}, final_output_data, upsert=True)
        st.write(f"Updated document id: {upload.upserted_id if upload.upserted_id else upload.modified_count}") 
        client.close()

    #----------------------------------------------------Data Transfer----------------------------------------------------
    st.subheader('Data Transfer')

    # Connect to the MongoDB server
    client = pymongo.MongoClient("mongodb+srv://praveensivakumar:1111@cluster0.jxaowcs.mongodb.net/")
    mydb = client['Youtube_DB']
    collection = mydb['Youtube_data']

    # Collect all document names and give them
    document_names = []
    for document in collection.find():
        document_names.append(document["Channel_Name"])
    document_name = st.selectbox(':red[**_Select Channel name :_**]', options = document_names, key='document_names')
    Data_Transfer = st.button('**Migrate to MySQL**')

    if Data_Transfer == True:
        # Retrieve the document with the specified name
        result = collection.find_one({"Channel_Name": document_name})
        client.close()

        # --------------------------------------------------------------- Data conversion ---------------------------------------------------------

        # Channel data json to df
        channel_details_to_sql = {
            "Channel_Name": result['Channel_Name'],
            "Channel_Id": result['_id'],
            "Video_Count": result['Channel_data']['Channel_Details']['Video_Count'],
            "Subscriber_Count": result['Channel_data']['Channel_Details']['Subscriber_Count'],
            "Channel_Views": result['Channel_data']['Channel_Details']['Channel_Views'],
            "Channel_Description": result['Channel_data']['Channel_Details']['Channel_Description'],
            "Playlist_Id": result['Channel_data']['Channel_Details']['Playlist_Id']
            }
        channel_df = pd.DataFrame.from_dict(channel_details_to_sql, orient='index').T
              
        # Playlist data json to df
        playlist_tosql = {
            "Channel_Id": result['_id'],
            "Playlist_Id": result['Channel_data']['Channel_Details']['Playlist_Id']
        }
        playlist_df = pd.DataFrame.from_dict(playlist_tosql, orient='index').T

        # Videos data json to df
        video_details_list = []
        for i in range(1,len(result['Channel_data'])-1):
            video_details_tosql = {
                'Playlist_Id':result['Channel_data']['Channel_Details']['Playlist_Id'],
                'Video_Id': result['Channel_data'][f"Video_Id_{i}"]['Video_Id'],
                'Video_Name': result['Channel_data'][f"Video_Id_{i}"]['Video_Name'],
                'Video_Description': result['Channel_data'][f"Video_Id_{i}"]['Video_Description'],
                'Published_date': result['Channel_data'][f"Video_Id_{i}"]['PublishedAt'],
                'View_Count': result['Channel_data'][f"Video_Id_{i}"]['View_Count'],
                'Like_Count': result['Channel_data'][f"Video_Id_{i}"]['Like_Count'],
                'Dislike_Count': result['Channel_data'][f"Video_Id_{i}"]['Dislike_Count'],
                'Favorite_Count': result['Channel_data'][f"Video_Id_{i}"]['Favorite_Count'],
                'Comment_Count': result['Channel_data'][f"Video_Id_{i}"]['Comment_Count'],
                'Duration': result['Channel_data'][f"Video_Id_{i}"]['Duration'],
                'Thumbnail': result['Channel_data'][f"Video_Id_{i}"]['Thumbnail'],
                'Caption_Status': result['Channel_data'][f"Video_Id_{i}"]['Caption_Status']
                }
            video_details_list.append(video_details_tosql)
        video_df = pd.DataFrame(video_details_list)

        # Comments data json to df
        Comment_details_list = []
        for i in range(1, len(result['Channel_data']) - 1):
            comments_access = result['Channel_data'][f"Video_Id_{i}"]['Comments']
            if comments_access == 'Unavailable' or ('Comment_Id_1' not in comments_access or 'Comment_Id_2' not in comments_access) :
                Comment_details_tosql = {
                    'Video_Id': 'Unavailable',
                    'Comment_Id': 'Unavailable',
                    'Comment_Text': 'Unavailable',
                    'Comment_Author':'Unavailable',
                    'Comment_Published_date': 'Unavailable',
                }
                Comment_details_list.append(Comment_details_tosql)
                
            else:
                for j in range(1,3):
                    Comment_details_tosql = {
                    'Video_Id': result['Channel_data'][f"Video_Id_{i}"]['Video_Id'],
                    'Comment_Id': result['Channel_data'][f"Video_Id_{i}"]['Comments'][f"Comment_Id_{j}"]['Comment_Id'],
                    'Comment_Text': result['Channel_data'][f"Video_Id_{i}"]['Comments'][f"Comment_Id_{j}"]['Comment_Text'],
                    'Comment_Author': result['Channel_data'][f"Video_Id_{i}"]['Comments'][f"Comment_Id_{j}"]['Comment_Author'],
                    'Comment_Published_date': result['Channel_data'][f"Video_Id_{i}"]['Comments'][f"Comment_Id_{j}"]['Comment_PublishedAt'],
                    }
                    Comment_details_list.append(Comment_details_tosql)
        Comments_df = pd.DataFrame(Comment_details_list)

        connect = mysql.connector.connect(
        host = "localhost",
        user = "root",
        password = "root",
        auth_plugin = "mysql_native_password")

        mycursor = connect.cursor()
        mycursor.execute("CREATE DATABASE IF NOT EXISTS youtube_db")

        mycursor.close()
        connect.close()

        engine = create_engine('mysql+mysqlconnector://root:root@localhost/youtube_db', echo=False)

        # Channel data
        channel_df.to_sql(
            'channel', 
            engine, 
            if_exists='append', 
            index=False,
            dtype = {
                "Channel_Name": sqlalchemy.types.VARCHAR(length=225),
                "Channel_Id": sqlalchemy.types.VARCHAR(length=225),
                "Video_Count": sqlalchemy.types.INT,
                "Subscriber_Count": sqlalchemy.types.BigInteger,
                "Channel_Views": sqlalchemy.types.BigInteger,
                "Channel_Description": sqlalchemy.types.TEXT,
                "Playlist_Id": sqlalchemy.types.VARCHAR(length=225),
            }
        )

        # Playlist data
        playlist_df.to_sql(
            'playlist', 
            engine, 
            if_exists='append', 
            index=False,
            dtype = {
                "Channel_Id": sqlalchemy.types.VARCHAR(length=225),
                "Playlist_Id": sqlalchemy.types.VARCHAR(length=225),
            }
        )

        # Videos data
        video_df.to_sql(
            'video', 
            engine, 
            if_exists='append', 
            index=False,
            dtype = {
                'Playlist_Id': sqlalchemy.types.VARCHAR(length=225),
                'Video_Id': sqlalchemy.types.VARCHAR(length=225),
                'Video_Name': sqlalchemy.types.VARCHAR(length=225),
                'Video_Description': sqlalchemy.types.TEXT,
                'Published_date': sqlalchemy.types.String(length=50),
                'View_Count': sqlalchemy.types.BigInteger,
                'Like_Count': sqlalchemy.types.BigInteger,
                'Dislike_Count': sqlalchemy.types.INT,
                'Favorite_Count': sqlalchemy.types.INT,
                'Comment_Count': sqlalchemy.types.INT,
                'Duration': sqlalchemy.types.VARCHAR(length=1024),
                'Thumbnail': sqlalchemy.types.VARCHAR(length=225),
                'Caption_Status': sqlalchemy.types.VARCHAR(length=225),
            }
        )

        # Comments data
        Comments_df.to_sql(
            'comments', 
            engine, 
            if_exists='append', 
            index=False,
            dtype = {
                'Video_Id': sqlalchemy.types.VARCHAR(length=225),
                'Comment_Id': sqlalchemy.types.VARCHAR(length=225),
                'Comment_Text': sqlalchemy.types.TEXT,
                'Comment_Author': sqlalchemy.types.VARCHAR(length=225),
                'Comment_Published_date': sqlalchemy.types.String(length=50),
            }
        )
        st.write(f"Data transfered to MySql")


#------------------------------------------------------Data Analysis-----------------------------------------------------
if selected == 'Data Analysis':
    mydb = mysql.connector.connect(
        host = "localhost",
        user = "root",
        password = "root",
        database = "youtube_db"
    )
    mycursor = mydb.cursor(buffered=True)
    st.subheader("Data Analysis")

    question = st.selectbox(':red[**_Available Questions :_**]',(
        '1. What are the names of all the videos and their corresponding channels?',
        '2. Which channels have the most number of videos, and how many videos do they have?',
        '3. What are the top 10 most viewed videos and their respective channels?',
        '4. How many comments were made on each video, and what are their corresponding video names?',
        '5. Which videos have the highest number of likes, and what are their corresponding channel names?',
        '6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?',
        '7. What is the total number of views for each channel, and what are their corresponding channel names?',
        '8. What are the names of all the channels that have published videos in the year 2022?',
        '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?',
        '10. Which videos have the highest number of comments, and what are their corresponding channel names?'
        ), key = 'collection_question')

    if question == '1. What are the names of all the videos and their corresponding channels?':
        mycursor.execute("SELECT channel.Channel_Name, video.Video_Name FROM channel JOIN playlist JOIN video ON channel.Channel_Id = playlist.Channel_Id AND playlist.Playlist_Id = video.Playlist_Id;")
        df = pd.DataFrame(mycursor.fetchall(), columns=['Channel Name', 'Video Name'])
        df.index += 1
        st.dataframe(df)

    if question == '2. Which channels have the most number of videos, and how many videos do they have?':
        mycursor.execute("SELECT Channel_Name, Video_Count FROM channel ORDER BY Video_Count DESC;")
        df = pd.DataFrame(mycursor.fetchall(),columns=['Channel Name','Video Count'])
        df.index += 1
        col1,col2 = st.columns(2)
        with col1:
            st.dataframe(df)
        with col2:
            fig = px.pie(
                df, 
                title='Channels with most number of videos',
                values='Video Count',
                names='Channel Name',
                color_discrete_sequence=px.colors.sequential.Agsunset,
                hover_data=['Video Count'],
                labels={'Video Count':'Video Count'}
            )

            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig,use_container_width=True)

    if question == '3. What are the top 10 most viewed videos and their respective channels?':
        mycursor.execute("SELECT channel.Channel_Name, video.Video_Name, video.View_Count FROM channel JOIN playlist ON channel.Channel_Id = playlist.Channel_Id JOIN video ON playlist.Playlist_Id = video.Playlist_Id ORDER BY video.View_Count DESC LIMIT 10;")
        df = pd.DataFrame(mycursor.fetchall(),columns=['Channel Name', 'Video Name', 'View count'])
        df.index += 1
        col1,col2 = st.columns(2)
        with col1:
            st.dataframe(df)
        with col2:
            fig = px.bar(
                df,
                title='Top 10 most viewed videos',
                x='Video Name',
                y='View count',
                #orientation='h',
                color='View count',
                color_continuous_scale=px.colors.sequential.Agsunset
            )
            st.plotly_chart(fig,use_container_width=True)

    if question == '4. How many comments were made on each video, and what are their corresponding video names?':
        mycursor.execute("SELECT channel.Channel_Name, video.Video_Name, video.Comment_Count FROM channel JOIN playlist ON channel.Channel_Id = playlist.Channel_Id JOIN video ON playlist.Playlist_Id = video.Playlist_Id;")
        df = pd.DataFrame(mycursor.fetchall(),columns=['Channel Name', 'Video Name', 'Comment count'])
        df.index += 1
        st.dataframe(df)

    if question == '5. Which videos have the highest number of likes, and what are their corresponding channel names?':
        mycursor.execute("SELECT channel.Channel_Name, video.Video_Name, video.Like_Count FROM channel JOIN playlist ON channel.Channel_Id = playlist.Channel_Id JOIN video ON playlist.Playlist_Id = video.Playlist_Id ORDER BY video.Like_Count DESC;")
        df = pd.DataFrame(mycursor.fetchall(),columns=['Channel Name', 'Video Name', 'Like count'])
        df.index += 1
        st.dataframe(df)

    if question == '6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?':
        st.write('**Note:- In November 2021, YouTube removed the public dislike count from all of its videos.**')
        mycursor.execute("SELECT channel.Channel_Name, video.Video_Name, video.Like_Count, video.Dislike_Count FROM channel JOIN playlist ON channel.Channel_Id = playlist.Channel_Id JOIN video ON playlist.Playlist_Id = video.Playlist_Id ORDER BY video.Like_Count DESC;")
        df = pd.DataFrame(mycursor.fetchall(),columns=['Channel Name', 'Video Name', 'Like count','Dislike count'])
        df.index += 1
        st.dataframe(df)

    if question == '7. What is the total number of views for each channel, and what are their corresponding channel names?':
        mycursor.execute("SELECT Channel_Name, Channel_Views FROM channel ORDER BY Channel_Views DESC;")
        df = pd.DataFrame(mycursor.fetchall(),columns=['Channel Name', 'Total number of views'])
        df.index += 1
        col1,col2 = st.columns(2)
        with col1:
            st.dataframe(df)
        with col2:
            fig = px.pie(
                df, 
                title='Total number of views for each channel',
                values='Total number of views',
                names='Channel Name',
                color_discrete_sequence=px.colors.sequential.Agsunset,
                hover_data=['Total number of views'],
                labels={'Total number of views':'Total number of views'}
            )

            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig,use_container_width=True)

    if question == '8. What are the names of all the channels that have published videos in the year 2022?':
        mycursor.execute("SELECT channel.Channel_Name, video.Video_Name, video.Published_date FROM channel JOIN playlist ON channel.Channel_Id = playlist.Channel_Id JOIN video ON playlist.Playlist_Id = video.Playlist_Id  WHERE EXTRACT(YEAR FROM Published_date) = 2022;")
        df = pd.DataFrame(mycursor.fetchall(),columns=['Channel Name','Video Name', 'Year 2022 only'])
        df.index += 1
        st.dataframe(df)

    if question == '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?':
        mycursor.execute("SELECT channel.Channel_Name, TIME_FORMAT(SEC_TO_TIME(AVG(TIME_TO_SEC(TIME(video.Duration)))), '%H:%i:%s') AS duration  FROM channel JOIN playlist ON channel.Channel_Id = playlist.Channel_Id JOIN video ON playlist.Playlist_Id = video.Playlist_Id GROUP by Channel_Name ORDER BY duration DESC ;")
        df = pd.DataFrame(mycursor.fetchall(),columns=['Channel Name','Average duration of videos'])
        df.index += 1
        col1,col2 = st.columns(2)
        with col1:
            st.dataframe(df)
        with col2:
            fig = px.bar(
                df,
                title='Average duration of all videos in a channel',
                x='Channel Name',
                y='Average duration of videos',
                #orientation='h',
                color='Average duration of videos',
                color_continuous_scale=px.colors.sequential.Agsunset
            )
            st.plotly_chart(fig,use_container_width=True)

    if question == '10. Which videos have the highest number of comments, and what are their corresponding channel names?':
        mycursor.execute("SELECT channel.Channel_Name, video.Video_Name, video.Comment_Count FROM channel JOIN playlist ON channel.Channel_Id = playlist.Channel_Id JOIN video ON playlist.Playlist_Id = video.Playlist_Id ORDER BY video.Comment_Count DESC;")
        df = pd.DataFrame(mycursor.fetchall(),columns=['Channel Name','Video Name', 'Number of comments'])
        df.index += 1
        st.dataframe(df)

    mydb.close()
#------------------------------------------------------About--------------------------------------------------------
if selected == 'About':
    st.subheader('About')
    st.markdown('''YouTube Data Harvesting and Warehousing is a user-friendly Streamlit application that utilizes the Google API to extract information on a YouTube channel, stores it in a MongoDB database, migrates it to a SQL data warehouse, and enables users to search for channel details and join tables to view data in the Streamlit app.''')
     
    st.markdown('**:red[Technologies]** : Python scripting, Data Collection, MongoDB, Streamlit, API integration, Data Managment using MongoDB (Atlas) and SQL')

    st.markdown('**:red[Domain]** : Social Media')


    st.markdown('**:red[Github Link]** : https://github.com/praveen-sivakumar/Youtube_Data_Harvesting_and_Warehousing')

    st.subheader('Project done by **:red[_Praveen Sivakumar_]**')
