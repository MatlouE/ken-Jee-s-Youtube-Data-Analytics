#So in this project we are building a web based dashboard for Ken_lee's Youtube 

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px 
import streamlit as st 
from datetime import datetime

# define functions
def style_negative(v, props=''):
    """Style negative values in dataframe"""
    pass

def style_positive(v, props=''):
    pass

def audience_simple(country):
    """Show top represented countries"""
    pass

#@st.cache #pre loaded data to save run time or something
def load_data():
    """Loads four dataframes and some light feature engineering"""
    
    #metrics of each video he has uploaded 
    df_agg = pd.read_csv("Aggregated_Metrics_By_Video.csv").iloc[1:,:]
    
    #feature engineering
    df_agg.columns = ['Video','Video_title','Video_publish_time','Comments_added','Shares','Dislikes','Likes',
                      'Subscribers_lost','Subscribers_gained','RPM(USD)','CPM(USD)','Average_%_viewed','Average_view_duration',
                      'Views','Watch_time (hours)','Subscribers','Your_estimated_revenue(USD)','Impressions','Impressions_ctr(%)']
    
    df_agg['Video_publish_time'] = pd.to_datetime(df_agg['Video_publish_time'], format='mixed')#converting to datetime
    
    df_agg['Average_view_duration'] = df_agg['Average_view_duration'].apply(lambda x: datetime.strptime(x, '%H:%M:%S'))
    df_agg['Avg_duration_sec'] = df_agg['Average_view_duration'].apply(lambda x: x.second + x.minute*60 + x.hour*3600)
    
    df_agg['Engagement_ratio'] = (df_agg['Comments_added'] + df_agg['Shares'] + df_agg['Dislikes'] + df_agg['Likes']) /df_agg.Views # Engagement out of total views
    df_agg['Views/sub_gained'] = df_agg['Views'] / df_agg['Subscribers_gained'] #views vs subs gained ratio
    df_agg.sort_values('Video_publish_time', ascending= False, inplace=True)
    
    #other datasets
    df_agg_sub = pd.read_csv("Aggregated_Metrics_By_Country_And_Subscriber_Status.csv")
    df_comments = pd.read_csv("All_Comments_Final.csv")
    df_time = pd.read_csv("Video_Performance_Over_Time.csv")
    df_time['Date'] = pd.to_datetime(df_time['Date'], format='mixed')
    
    return df_agg, df_agg_sub, df_comments, df_time
#basically returning our feature engineered dataframes

df_agg, df_agg_sub, df_comments, df_time = load_data()

#additional data engineering for aggregatted data
df_agg_diff = df_agg.copy()
metric_date_12mo = df_agg_diff['Video_publish_time'].max() - pd.DateOffset(months=12)

# Filter rows
filtered_df = df_agg_diff[df_agg_diff['Video_publish_time'] >= metric_date_12mo]

# Select only numeric columns
numeric_cols = filtered_df.select_dtypes(include=[np.number])

# Compute median across rows (axis=0 → column-wise median)
median_agg = np.median(numeric_cols, axis=0)
#create differences from the median for values
#just numeric columns
#merge daily data with publish data to get delta
#merging df_time dataset with df_agg but just the two related columns as foreign keys
df_time_diff = pd.merge(df_time, df_agg,left_on = 'External Video ID', right_on='Video', how='left')
df_time_diff['days_published'] = (df_time_diff['Date'] - df_time_diff['Video_publish_time']).dt.days

#get last 12months of data rather than all data
date_12mo = df_agg['Video_publish_time'].max() - pd.DateOffset(months=12)
df_time_diff_yr =  df_time_diff[df_time_diff['Video_publish_time'] >= date_12mo]
                                 
#get daily view data first 30 median & percentiles
views_days = pd.pivot_table(
    df_time_diff_yr,
    index='days_published',
    values='Views_x',
    aggfunc=[np.mean, np.median, lambda x: np.percentile(x, 80), lambda x: np.percentile(x, 20)]
).reset_index()

views_days.columns = ['days_published','mean_views','median_views','80pct_views','20pct_views']
views_days = views_days[views_days['days_published'].between(0, 30)]
views_cumulative = views_days.loc[:, ['days_published', 'median_views','80pct_views', '20pct_views']]
views_cumulative.loc[:, ['median_views', '80pct_views', '20pct_views']] = views_cumulative.loc[:, ['median_views', '80pct_views', '20pct_views']].cumsum()


#Building Our Streamlit app


add_sidebar = st.sidebar.selectbox('Aggregate or Individual Video', ('Aggregate Metrics', 'Individual Video Analysis'))

#show individual Metrics
if add_sidebar == 'Aggregate Metrics':
    st.write("Ken Lee YouTube Aggregated Data")
    
    ##Getting metrics to show on our Dashboard
    df_agg_metrics = df_agg[['Video_publish_time','Views','Likes','Subscribers','Shares','Comments_added','RPM(USD)','Average_%_viewed',
                             'Avg_duration_sec', 'Engagement_ratio','Views/sub_gained']]
    
    #calculate medians for last 6 and 12 months
    metric_date_6mo = df_agg_metrics['Video_publish_time'].max() - pd.DateOffset(months=6)
    metric_date_12mo = df_agg_metrics['Video_publish_time'].max() - pd.DateOffset(months=12)
    metric_medians6mo = df_agg_metrics[df_agg_metrics['Video_publish_time'] >= metric_date_6mo].median()
    metric_medians12mo = df_agg_metrics[df_agg_metrics['Video_publish_time'] >= metric_date_12mo].median()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    columns = [col1, col2, col3, col4, col5]

    count = 0
    for i in metric_medians6mo.index:
        with columns[count]:
            delta = (metric_medians6mo[i] - metric_medians12mo[i])/metric_medians12mo[i] #delta - the difference between two values in
            # this case delta is the percentage change between the 6month median and 12 month median
            st.metric(label=i, value= f"{metric_medians6mo[i]:.2f}", delta= f"{delta:.2%}")
            count += 1
            if count >= 5:
                count = 0

if add_sidebar == 'Individual Video Analysis':
    st.write("Ken Lee YouTube Aggregated Data")