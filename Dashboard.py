#So in this project we are building a web based dashboard for Ken_lee's Youtube 

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px 
import streamlit as st 
from datetime import datetime

# define functions
def style_negative(v, props=''):
    """ Style negative values in dataframe"""
    try: 
        return props if v < 0 else None
    except:
        pass

def style_positive(v, props=''):
    """Style positive values in dataframe"""
    try: 
        return props if v > 0 else None
    except:
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

df_agg_diff.iloc[:numeric_cols] = (df_agg_diff.iloc[:numeric_cols] - median_agg).div(median_agg)
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
    if add_sidebar == 'Aggregate Metrics':
    # Ensure datetime and fix column typo
        df_agg['Video_publish_time'] = pd.to_datetime(df_agg['Video_publish_time'], dayfirst=False , errors='coerce')

        # Select only existing columns and numeric metrics
        metric_cols = [
            'Views', 'Likes', 'Subscribers', 'Shares', 'Comments_added', 'RPM(USD)',
            'Average_%_viewed', 'Avg_duration_sec', 'Engagement_ratio', 'Views/sub_gained'
        ]
        df_agg_metrics = df_agg[['Video_publish_time'] + metric_cols].copy()

        # Date ranges
        latest_date = df_agg_metrics['Video_publish_time'].max()
        metric_date_6mo = latest_date - pd.DateOffset(months=6)
        metric_date_12mo = latest_date - pd.DateOffset(months=12)

        # Filter windows
        df_6mo = df_agg_metrics[df_agg_metrics['Video_publish_time'] >= metric_date_6mo]
        df_12mo = df_agg_metrics[df_agg_metrics['Video_publish_time'] >= metric_date_12mo]

        # Compute medians for numeric columns only
        metric_medians6mo = df_6mo[metric_cols].median(numeric_only=True)
        metric_medians12mo = df_12mo[metric_cols].median(numeric_only=True)

        # Align indices (should already match metric_cols)
        metric_medians6mo = metric_medians6mo.reindex(metric_cols)
        metric_medians12mo = metric_medians12mo.reindex(metric_cols)

        # Streamlit layout
        col1, col2, col3, col4, col5 = st.columns(5)
        columns = [col1, col2, col3, col4, col5]

        count = 0
        for i in metric_cols:
            with columns[count]:
                val_6 = metric_medians6mo[i]
                val_12 = metric_medians12mo[i]

                # Safe delta calculation: handle NaN and zero
                if pd.isna(val_6) or pd.isna(val_12) or val_12 == 0:
                    delta_str = "—"
                else:
                    delta = (val_6 - val_12) / val_12
                    delta_str = "{:.2%}".format(delta)

                st.metric(label=i, value=None if pd.isna(val_6) else round(val_6, 1), delta=delta_str)

            count += 1
            if count >= 5:
                count = 0
                
        df_agg_diff['Publish_date'] = df_agg_diff['Video_publish_time'].apply(lambda x: x.date)
        df_agg_diff_final = df_agg_diff.loc[:, ['Video_title', 'Publish_date','Comments_added','Shares','Dislikes','Likes',
                                            'Subscribers_lost','Subscribers_gained']]

        st.dataframe(df_agg_diff_final)                          
                        

if add_sidebar == 'Individual Video Analysis':
    st.write("Invidiual Video Analysis")

    videos = tuple(df_agg['Video_title'])
    video_select = st.sidebar.selectbox('Select Video', videos)

    agg_filtered = df_agg[df_agg['Video_title'] == video_select]
    agg_sub_filtered = df_agg_sub[df_agg_sub['Video_title'] == video_select]
    agg_sub_filtered['Country'] = agg_sub_filtered['Country']