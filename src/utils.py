import os
import sys
import glob
import json
import datetime
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from nltk.corpus import stopwords
from wordcloud import WordCloud


def break_combined_weeks(combined_weeks):
    """
    Breaks combined weeks into separate weeks.
    
    Args:
        combined_weeks: list of tuples of weeks to combine
        
    Returns:
        tuple of lists of weeks to be treated as plus one and minus one
    """
    plus_one_week = []
    minus_one_week = []

    for week in combined_weeks:
        if week[0] < week[1]:
            plus_one_week.append(week[0])
            minus_one_week.append(week[1])
        else:
            minus_one_week.append(week[0])
            plus_one_week.append(week[1])

    return plus_one_week, minus_one_week

def get_msgs_df_info(df):
    msgs_count_dict = df.user.value_counts().to_dict()
    replies_count_dict = dict(Counter([u for r in df.replies if r != None for u in r]))
    mentions_count_dict = dict(Counter([u for m in df.mentions if m != None for u in m]))
    links_count_dict = df.groupby("user").link_count.sum().to_dict()
    return msgs_count_dict, replies_count_dict, mentions_count_dict, links_count_dict



def get_messages_dict(msgs):
    msg_list = {
            "msg_id":[],
            "text":[],
            "attachments":[],
            "user":[],
            "mentions":[],
            "emojis":[],
            "reactions":[],
            "replies":[],
            "replies_to":[],
            "ts":[],
            "links":[],
            "link_count":[]
            }


    for msg in msgs:
        if "subtype" not in msg:
            try:
                msg_list["msg_id"].append(msg["client_msg_id"])
            except:
                msg_list["msg_id"].append(None)
            
            msg_list["text"].append(msg["text"])
            msg_list["user"].append(msg["user"])
            msg_list["ts"].append(msg["ts"])
            
            if "reactions" in msg:
                msg_list["reactions"].append(msg["reactions"])
            else:
                msg_list["reactions"].append(None)

            if "parent_user_id" in msg:
                msg_list["replies_to"].append(msg["ts"])
            else:
                msg_list["replies_to"].append(None)

            if "thread_ts" in msg and "reply_users" in msg:
                msg_list["replies"].append(msg["replies"])
            else:
                msg_list["replies"].append(None)
            
            if "blocks" in msg:
                emoji_list = []
                mention_list = []
                link_count = 0
                links = []
                
                for blk in msg["blocks"]:
                    if "elements" in blk:
                        for elm in blk["elements"]:
                            if "elements" in elm:
                                for elm_ in elm["elements"]:
                                    
                                    if "type" in elm_:
                                        if elm_["type"] == "emoji":
                                            emoji_list.append(elm_["name"])

                                        if elm_["type"] == "user":
                                            mention_list.append(elm_["user_id"])
                                        
                                        if elm_["type"] == "link":
                                            link_count += 1
                                            links.append(elm_["url"])


                msg_list["emojis"].append(emoji_list)
                msg_list["mentions"].append(mention_list)
                msg_list["links"].append(links)
                msg_list["link_count"].append(link_count)
            else:
                msg_list["emojis"].append(None)
                msg_list["mentions"].append(None)
                msg_list["links"].append(None)
                msg_list["link_count"].append(0)
    
    return msg_list

def from_msg_get_replies(msg):
    replies = []
    if "thread_ts" in msg and "replies" in msg:
        try:
            for reply in msg["replies"]:
                reply["thread_ts"] = msg["thread_ts"]
                reply["message_id"] = msg["client_msg_id"]
                replies.append(reply)
        except:
            pass
    return replies

def msgs_to_df(msgs):
    msg_list = get_messages_dict(msgs)
    df = pd.DataFrame(msg_list)
    return df

def process_msgs(msg):
    '''
    select important columns from the message
    '''

    keys = ["client_msg_id", "type", "text", "user", "ts", "team", 
            "thread_ts", "reply_count", "reply_users_count"]
    msg_list = {k:msg[k] for k in keys}
    rply_list = from_msg_get_replies(msg)

    return msg_list, rply_list

def get_messages_from_channel(channel_path):
    '''
    get all the messages from a channel        
    '''
    channel_json_files = os.listdir(channel_path)
    channel_msgs = [json.load(open(channel_path + "/" + f)) for f in channel_json_files]

    df = pd.concat([pd.DataFrame(get_messages_dict(msgs)) for msgs in channel_msgs])
    print(f"Number of messages in channel: {len(df)}")
    
    return df


def convert_2_timestamp(column, data):
    """convert from unix time to readable timestamp
        args: column: columns that needs to be converted to timestamp
                data: data that has the specified column
    """
    if column in data.columns.values:
        timestamp_ = []
        for time_unix in data[column]:
            if time_unix == 0:
                timestamp_.append(0)
            else:
                a = datetime.datetime.fromtimestamp(float(time_unix))
                timestamp_.append(a.strftime('%Y-%m-%d %H:%M:%S'))
        return timestamp_
    else: print(f"{column} not in data")

def get_tagged_users(df):
    return df['msg_content'].str.findall(r'@U\w+').explode().unique().tolist()

def map_userid_2_realname(user_profile: dict, comm_dict: dict, plot=False):
    user_dict = {user['id']: user['real_name'] for user in user_profile['profile']}
    
    mapped_comm_dict = {user_dict.get(user_id, user_id): count for user_id, count in comm_dict.items()}

    mapped_comm_df = pd.DataFrame(list(mapped_comm_dict.items()), columns=['LearnerName', '# of Msg sent in Threads']) \
        .sort_values(by='# of Msg sent in Threads', ascending=False)

    if plot:
        mapped_comm_df.plot.bar(figsize=(15, 7.5), x='LearnerName', y='# of Msg sent in Threads')
        plt.title('Student based on Message sent in thread', size=20)
        plt.show()

    return mapped_comm_df

def get_top_20_user(data, channel='Random'):
    data['sender_name'].value_counts()[:20].plot.bar(figsize=(15, 7.5))
    plt.title(f'Top 20 Message Senders in #{channel} channels', size=15, fontweight='bold')
    plt.xlabel("Sender Name", size=18); plt.ylabel("Frequency", size=14);
    plt.xticks(size=12); plt.yticks(size=12);
    plt.show()

def draw_avg_reply_count(data, channel='Random'):
    data.groupby('sender_name')['reply_count'].mean().sort_values(ascending=False)[:20] \
        .plot(kind='bar', figsize=(15, 7.5))
    plt.title(f'Average Number of reply count per Sender in #{channel}', size=20, fontweight='bold')
    plt.xlabel("Sender Name", size=18); plt.ylabel("Frequency", size=18);
    plt.xticks(size=14); plt.yticks(size=14);
    plt.show()

def draw_avg_reply_users_count(data, channel='Random'):
    data.groupby('sender_name')['reply_users_count'].mean().sort_values(ascending=False)[:20].plot(kind='bar',
        figsize=(15, 7.5))
    plt.title(f'Average Number of reply user count per Sender in #{channel}', size=20, fontweight='bold')
    plt.xlabel("Sender Name", size=18); plt.ylabel("Frequency", size=18);
    plt.xticks(size=14); plt.yticks(size=14);
    plt.show()

def draw_wordcloud(msg_content, week):    
    all_words = ' '.join(msg_content)
    wordcloud = WordCloud(background_color='#975429', width=500, height=300, random_state=21, max_words=500,
                          mode='RGBA', max_font_size=140, stopwords=stopwords.words('english')).generate(all_words)
    plt.figure(figsize=(15, 7.5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis('off')
    plt.tight_layout()
    plt.title(f'WordCloud for {week}', size=30)
    plt.show()

def draw_user_reaction(data, channel='General'):
    data.groupby('sender_name')[['reply_count', 'reply_users_count']].sum() \
        .sort_values(by='reply_count', ascending=False)[:10].plot(kind='bar', figsize=(15, 7.5))
    plt.title(f'User with the most reaction in #{channel}', size=25)
    plt.xlabel("Sender Name", size=18); plt.ylabel("Frequency", size=18);
    plt.xticks(size=14); plt.yticks(size=14);
    plt.show()


