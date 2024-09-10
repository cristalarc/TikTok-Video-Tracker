We need to create Python based software that helps track the performance of TikTok Videos over time.
The user will provide on a daily basis an export file that is provided by TikTok. This will be an .xlsx file containing data about the performance of TikTok videos for the Date Range mentioned in the file.
    
Our tool needs to keep a record over time of any video that has more than 4000 video views on a given day. In example, if video A has 200 views today, the video will not be ingested. If the next day it has 4200 views, the video must be ingested, and tracking needs to continue no matter how many views it has the following days.
Once a video is ingested, we must keep track of all the metrics given by the videodetails_tiktok_export file.
    
The software should also have search capabilities so that videos can be easily searched. 
The software should also have plotting capabilities. When I choose a specific video, I should be able to see a graph that plots the performance over time of that video for a chosen metric.
    
The metrics to track are the following VV, Likes, Comments, Shares, New followers, V-to-L clicks, Product Impressions, Product Clicks, Buyers, Orders, Unit Sales, Video Revenue ($), GPM ($), Shoppable video attributed GMV ($), CTR, V-to-L rate, Video Finish Rate, CTOR.

The software needs to have buttons that trigger the upload of Videodetails_tiktok_export.xlsx which will be facilitated by a window that allows the user to select the file to upload.