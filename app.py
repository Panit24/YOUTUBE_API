from re import A
from urllib import request
from googleapiclient.discovery import build
import pandas as pd
from IPython.display import JSON
import json
import seaborn as sns
import matplotlib.pyplot as plt
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context
# NLP libraries
import nltk
from nltk.corpus import stopwords
# from nltk.tokenize import word_tokenize
nltk.download()
# nltk.download('stopwords')
# nltk.download('punkt')
from wordcloud import WordCloud
api_key = 'AIzaSyDdmLezdHwTA996Hch-Xy9Qes1zRPcTH-Q'
# channel_ids = ['UCqkeU8psATW3SP_xhgeeN8A','DOHOMECHANNEL','Globalhousethai','NocNocTH','homeprothai']
channel_ids = ['UCqkeU8psATW3SP_xhgeeN8A',"UC_x5XG1OV2P6uZZ5FSM9Ttw"] #Google developer and Thaiwatsadu
# channel_ids = ['UCoOae5nYA7VqaXzerajD0lg'] #Ali


api_service_name = "youtube" 
api_version = "v3"

youtube = build(
  api_service_name, api_version, developerKey=api_key)

def get_channel_stats(youtube,channel_ids):
  all_data = []
  
  request = youtube.channels().list(
          part="snippet,contentDetails,statistics",
          id=','.join(channel_ids)
  )
  response = request.execute()
  # JSON(response)
  # print(JSON(response))
  # print((type(response)))
  # print(json.dumps(response,indent=4))


  for item in response['items']:
    data = {'channelName': item["snippet"]["title"],
            'subscribers':item["statistics"]["subscriberCount"],
            'views':item["statistics"]['viewCount'],
            'totalVideos':item['statistics']["videoCount"],
            'playlistId':item['contentDetails']['relatedPlaylists']['uploads']
    }
    all_data.append(data)
  
  return(pd.DataFrame(all_data))

channel_stats = get_channel_stats(youtube,channel_ids)


# print(channel_stats)
#--------------------------------------
playlist_id = "UUqkeU8psATW3SP_xhgeeN8A" #Thaiwatsadu
# playlist_id = "UUoOae5nYA7VqaXzerajD0lg" #Ali

def get_videos_ids(youtube,playlist_id):
  videos_ids = []

  request = youtube.playlistItems().list(
          part="snippet,contentDetails",
          playlistId=playlist_id,
          maxResults= 50
  )
  response = request.execute()
  
  for item in response['items']:
    videos_ids.append(item['contentDetails']['videoId'])
  next_page_token = response.get('nextPageToken')
  while next_page_token is not None:
    request = youtube.playlistItems().list(
      part="contentDetails",
      playlistId = playlist_id,
      maxResults = 50,
      pageToken = next_page_token)
    response = request.execute()
    
    for item in response['items']:
        videos_ids.append(item['contentDetails']['videoId'])
        
    next_page_token = response.get('nextPageToken')
    
  return videos_ids
#Get video IDs
video_ids = get_videos_ids(youtube, playlist_id)
# print(video_ids)
# print(len(video_ids))
#--------------------------------------
#Get video details
def get_video_details(youtube,video_ids):
  all_video_info = []
  for i in range(0,len(video_ids),50):
    
    request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id = ','.join(video_ids[i:i+50])
    )
    response = request.execute()
    # print(json.dumps(response,indent=4))
    for video in response['items']:
      stats_to_keep = {'snippet':['channelTitle','title',"description",'tags','publishedAt'],
                      "statistics":['viewCount','likeCount','favouriteCount','commentCount'],
                      'contentDetails':['duration','definition','caption']}
      video_info = {} 
      video_info['video_id'] = video['id']
      
      for k in stats_to_keep.keys():
        for v in stats_to_keep[k]:
          try:
            video_info[v] = video[k][v]
          except:
            video_info[v] = None
      all_video_info.append(video_info)
  return pd.DataFrame(all_video_info)
video_df = get_video_details(youtube,video_ids)
# print(video_df)
#--------------------------------------

# def get_comments_in_videos(youtube, video_ids):
#     """
#     Get top level comments as text from all videos with given IDs (only the first 10 comments due to quote limit of Youtube API)
#     Params:
    
#     youtube: the build object from googleapiclient.discovery
#     video_ids: list of video IDs
    
#     Returns:
#     Dataframe with video IDs and associated top level comment in text.
    
#     """
#     all_comments = []
    
#     for video_id in video_ids:
#         try:   
#             request = youtube.commentThreads().list(
#                 part="snippet,replies",
#                 videoId=video_id
#             )
#             response = request.execute()
        
#             comments_in_video = [comment['snippet']['topLevelComment']['snippet']['textOriginal'] for comment in response['items'][0:10]]
#             comments_in_video_info = {'video_id': video_id, 'comments': comments_in_video}

#             all_comments.append(comments_in_video_info)
            
#         except: 
#             # When error occurs - most likely because comments are disabled on a video
#             print('Could not get comments for video ' + video_id)
        
#     return pd.DataFrame(all_comments)  
# comments_df = get_comments_in_videos(youtube,video_ids) #df data frame
# print(comments_df)
# print(comments_df['comments'][0])
#--------------------------------------
# print(video_df.isnull().any())
# print(video_df.dtypes)
numeric_cols = ['viewCount','likeCount','favouriteCount','commentCount']
video_df[numeric_cols] = video_df[numeric_cols].apply(pd.to_numeric,errors = 'coerce',axis = 1)
#publish day in the week
from dateutil import parser
video_df['publishedAt'] = video_df['publishedAt'].apply(lambda x: parser.parse(x)) 
video_df['pushblishDayName'] = video_df['publishedAt'].apply(lambda x: x.strftime("%A")) #%A full week day name
#Convert duration to seconds
# import isodate
# video_df["durationSecs"] = video_df['duraton'].apply(lambda x:isodate.parse_duration(x))
# video_df["durationSecs"] = video_df['duratonSecs'].astype('timedelta64[s]')
import isodate
video_df['durationSecs'] = video_df['duration'].apply(lambda x: isodate.parse_duration(x))
video_df['durationSecs'] = video_df['durationSecs'].astype('timedelta64[s]')
# print(video_df[['durationSecs','duration']])

video_df['tagCount'] = video_df['tags'].apply(lambda x: 0 if x is None else len(x))
# print(video_df)

#--------------------------------------
# ax = sns.barplot(x = 'title',y = 'viewCount', data = video_df.sort_values('viewCount',ascending=False)[0:9])
# plot = ax.set_xticklabels(ax.get_xticklabels(),rotation=90)
#--------------------------------------
# sns.violinplot(x=video_df['channelTitle'],y= video_df['viewCount'],scale="count")
#--------------------------------------
# fig, ax =plt.subplots(1,2)
# sns.scatterplot(data = video_df, x = "commentCount", y = "viewCount", ax=ax[0])
# sns.scatterplot(data = video_df, x = "likeCount", y = "viewCount", ax=ax[1])
#--------------------------------------
# sns.histplot(data = video_df, x = "durationSecs",bins=30)
# plt.show()
#--------------------------------------
stop_words = set(stopwords.words('english'))
video_df['title_no_stopwords'] = video_df['title'].apply(lambda x: [item for item in str(x).split() if item not in stop_words])

all_words = list([a for b in video_df['title_no_stopwords'].tolist() for a in b])
all_words_str = ' '.join(all_words) 

def plot_cloud(wordcloud):
    plt.figure(figsize=(30, 20))
    plt.imshow(wordcloud) 
    plt.axis("off");

wordcloud = WordCloud(width = 2000, height = 1000, random_state=1, background_color='black', 
                      colormap='viridis', collocations=False).generate(all_words_str)
plot_cloud(wordcloud)
plt.show()
#--------------------------------------

# day_df = pd.DataFrame(video_df['pushblishDayName'].value_counts())
# weekdays = [ 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
# day_df = day_df.reindex(weekdays)
# ax = day_df.reset_index().plot.bar(x='index', y='pushblishDayName', rot=0)
# plt.show()


 
      





  
  



  