import os
import sys
import glob
import json
import datetime
from collections import Counter
from collections import Counter

import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from nltk.corpus import stopwords

def generate_random_message_id(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

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

def get_mentions_from_messages(msgs):
    """
    Extract user mentions from a list of Slack messages.

    Args:
        msgs (list): List of Slack messages.

    Returns:
        list: List of lists, each containing user IDs mentioned in a message.
    """
    mentions_list = []

    for msg in msgs:
        if "subtype" not in msg and "blocks" in msg:
            mention_list = []

            for blk in msg["blocks"]:
                if "elements" in blk:
                    for elm in blk["elements"]:
                        if "elements" in elm:
                            for elm_ in elm["elements"]:
                                if "type" in elm_ and elm_["type"] == "user":
                                    mention_list.append(elm_["user_id"])

            mentions_list.append(mention_list)

    return mentions_list

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

def get_mention_count_from_messages(msgs):
    """
    Extract user mentions from a list of Slack messages.

    Args:
        msgs (list): List of Slack messages.

    Returns:
        list: List of dictionaries, each containing message ID, text, and mentions count.
    """
    mentions_list = []

    for msg in msgs:
        if "subtype" not in msg and "blocks" in msg:
            mention_list = []

            for blk in msg["blocks"]:
                if "elements" in blk:
                    for elm in blk["elements"]:
                        if "elements" in elm:
                            for elm_ in elm["elements"]:
                                if "type" in elm_ and elm_["type"] == "user":
                                    mention_list.append(elm_["user_id"])

            message_id = msg.get("client_msg_id", generate_random_message_id())
            text = msg.get("text", "")

            message_data = {
                "message_id": message_id,
                "text": text,
                "mentions_count": len(mention_list),
            }

            
            mentions_list.append(message_data)

    return mentions_list


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

def process_message(msg):
    '''
    select important columns from the message
    '''

    keys = [ "text", "ts"]
    msg_list = {k:msg[k] for k in keys}
    rply_list = from_msg_get_replies(msg)
    # print(msg_list)

    return msg_list, rply_list

def user_reply_count_on_channel(path_channel):
    """
    Count the number of replies from each user in a Slack channel based on JSON data.

    Args:
        path_channel (str): The path to the directory containing Slack JSON files.

    Returns:
        dict: A dictionary mapping user IDs to their reply count.
    """

    json_files = [
        f"{path_channel}/{pos_json}" 
        for pos_json in os.listdir(path_channel) 
        if pos_json.endswith('.json')
    ]    
    combined = []

    for json_file in json_files:
        with open(json_file, 'r', encoding="utf8") as slack_data:
            json_content = json.load(slack_data)
            combined.extend(json_content)

    channel_users_reply_count = {}

    for row in combined:
        if 'bot_id' in row.keys():
            continue
        elif 'reply_users' in row.keys():
            for user_id in row["reply_users"]:
                channel_users_reply_count[user_id] = channel_users_reply_count.get(user_id, 0) + 1

    return channel_users_reply_count

def get_channel_messages_replies_timestamp(channel_path):

    json_files = [
        f"{channel_path}/{pos_json}" 
        for pos_json in os.listdir(channel_path) 
        if pos_json.endswith('.json')
    ]   

    combined = []

    for json_file in json_files:
        with open(json_file, 'r', encoding="utf8") as slack_data:
            json_content = json.load(slack_data)
            combined.extend(json_content)
    
    reply_timestamps = []

    for msg in combined:    
        msg_reply = from_msg_get_replies(msg) 
        if msg_reply: 
            reply_timestamps.append(msg_reply)


    return reply_timestamps


def get_messages_from_channel(channel_path):
    '''
    get all the messages from a channel        
    '''
    channel_json_files = os.listdir(channel_path)
    channel_msgs = [json.load(open(channel_path + "/" + f)) for f in channel_json_files]

    df = pd.concat([pd.DataFrame(get_messages_dict(msgs)) for msgs in channel_msgs])
    print(f"Number of messages in channel: {len(df)}")
    
    return df

def get_messages_reply_timestamp_from_channel(channel_path):
    """
    Get timestamps of messages along with their latest reply timestamps from a Slack channel.

    Args:
        channel_path (str): The path to the directory containing Slack JSON files for the channel.

    Returns:
        tuple: A tuple containing a list of message timestamps along with their latest reply timestamps
               and the count of messages with no replies.
    """
    json_files = [
        f"{channel_path}/{pos_json}" 
        for pos_json in os.listdir(channel_path) 
        if pos_json.endswith('.json')
    ]     
    combined = []

    for json_file in json_files:
        with open(json_file, 'r', encoding="utf8") as slack_data:
            json_content = json.load(slack_data)
            combined.extend(json_content)
    
    message_time_stamps = []
    no_reply_messages_count = 0

    for msgs in combined:
        if "latest_reply" in msgs:
            message_time_stamps.append([msgs["ts"], msgs["latest_reply"]])
        else:
            no_reply_messages_count += 1

    return message_time_stamps, no_reply_messages_count

def get_user_mentions_from_channel(channel_path):
    """
    Get mentions count of users from a Slack channel.

    Args:
        channel_path (str): The path to the directory containing Slack JSON files for the channel.

    Returns:
        dict: A dictionary mapping user IDs to their mentions count.
    """
    json_files = [
        f"{channel_path}/{pos_json}" 
        for pos_json in os.listdir(channel_path) 
        if pos_json.endswith('.json')
    ]
    channel_users_mentions_count = {}

    for json_file in json_files:
        with open(json_file, 'r', encoding="utf8") as slack_data:
            json_content = json.load(slack_data)

            mentions_list = get_mentions_from_messages(json_content)
            for mentions in mentions_list:
                for user_id in mentions:
                    if user_id:
                        channel_users_mentions_count[user_id] = channel_users_mentions_count.get(user_id, 0) + 1

    return channel_users_mentions_count

def get_message_mentions_count_from_channel(channel_path):
    """
    Get messages with their count of mentions from a Slack channel.

    Args:
        channel_path (str): The path to the directory containing Slack JSON files for the channel.

    Returns:
        list: List of dictionaries, each containing message ID, text, and mentions count.
    """
     
    json_files = [
        f"{channel_path}/{pos_json}" 
        for pos_json in os.listdir(channel_path) 
        if pos_json.endswith('.json')
    ]
    combined = []

    for json_file in json_files:
        with open(json_file, 'r', encoding="utf8") as slack_data:
            json_content = json.load(slack_data)
            combined.extend(json_content)
    

    channel_message_metions_count = []
    channel_message_metions_count = get_mention_count_from_messages(combined)
                 
    return channel_message_metions_count

def get_user_message_count_from_channel(channel_path):
    """
    Get message count of users from a Slack channel.

    Args:
        channel_path (str): The path to the directory containing Slack JSON files for the channel.

    Returns:
        dict: A dictionary mapping user IDs to their message count.
    """
    json_files = [
        f"{channel_path}/{pos_json}" 
        for pos_json in os.listdir(channel_path) 
        if pos_json.endswith('.json')
    ]
    combined = []

    for json_file in json_files:
        with open(json_file, 'r', encoding="utf8") as slack_data:
            json_content = json.load(slack_data)
            combined.extend(json_content)

    channel_users_message_count = {}

    for msgs in combined:
        user_id = msgs["user"]
        channel_users_message_count[user_id] = channel_users_message_count.get(user_id, 0) + 1

    return channel_users_message_count


def get_user_reaction_count_from_channel(channel_path):
    """
    Get the count of reactions per user from a Slack channel.

    Args:
        channel_path (str): The path to the directory containing Slack JSON files for the channel.

    Returns:
        dict: A dictionary mapping user IDs to their reaction count.
    """
    json_files = [
        f"{channel_path}/{pos_json}" 
        for pos_json in os.listdir(channel_path) 
        if pos_json.endswith('.json')
    ]
    combined = []

    for json_file in json_files:
        with open(json_file, 'r', encoding="utf8") as slack_data:
            json_content = json.load(slack_data)
            combined.extend(json_content)

    channel_users_reactions_count = {}

    for msg in combined:
        if "subtype" not in msg and "reactions" in msg:
            for reaction in msg["reactions"]:
                for user_id in reaction["users"]:
                    channel_users_reactions_count[user_id] = channel_users_reactions_count.get(user_id, 0) + 1

    return channel_users_reactions_count


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
    """get all @ in the messages"""

    return df['msg_content'].map(lambda x: re.findall(r'@U\w+', x))


    
def map_userid_2_realname(user_profile: dict, comm_dict: dict, plot=False):
    """
    map slack_id to realnames
    user_profile: a dictionary that contains users info such as real_names
    comm_dict: a dictionary that contains slack_id and total_message sent by that slack_id
    """
    user_dict = {} # to store the id
    real_name = [] # to store the real name
    ac_comm_dict = {} # to store the mapping
    count = 0
    # collect all the real names
    for i in range(len(user_profile['profile'])):
        real_name.append(dict(user_profile['profile'])[i]['real_name'])

    # loop the slack ids
    for i in user_profile['id']:
        user_dict[i] = real_name[count]
        count += 1

    # to store mapping
    for i in comm_dict:
        if i in user_dict:
            ac_comm_dict[user_dict[i]] = comm_dict[i]

    ac_comm_dict = pd.DataFrame(data= zip(ac_comm_dict.keys(), ac_comm_dict.values()),
    columns=['LearnerName', '# of Msg sent in Threads']).sort_values(by='# of Msg sent in Threads', ascending=False)
    
    if plot:
        ac_comm_dict.plot.bar(figsize=(15, 7.5), x='LearnerName', y='# of Msg sent in Threads')
        plt.title('Student based on Message sent in thread', size=20)
        
    return ac_comm_dict


def extract_timestamps(msg):
    timestamps = [msg["ts"]]
        

    if "thread_ts" in msg and "replies" in msg:
        for reply in msg["replies"]:
            timestamps.append(reply["ts"])

    return timestamps

def get_timestamps_from_messages(msgs):
    all_timestamps = []

    for msg in msgs:
        if "subtype" not in msg:
            timestamps = extract_timestamps(msg)
            all_timestamps.extend(timestamps)

    return all_timestamps

def get_all_events_timestamp_on_channel(channel_path):

    json_files = [
        f"{channel_path}/{pos_json}" 
        for pos_json in os.listdir(channel_path) 
        if pos_json.endswith('.json')
    ]
    combined = []

    for json_file in json_files:
        with open(json_file, 'r', encoding="utf8") as slack_data:
            json_content = json.load(slack_data)
            combined.extend(json_content)
    
    channel_events_time_stamp = get_timestamps_from_messages(combined)
                 
    return channel_events_time_stamp

def get_messages_on_channel(channel_path):

    json_files = [
        f"{channel_path}/{pos_json}" 
        for pos_json in os.listdir(channel_path) 
        if pos_json.endswith('.json')
    ]
    combined = []

    for json_file in json_files:
        with open(json_file, 'r', encoding="utf8") as slack_data:
            json_content = json.load(slack_data)
            combined.extend(json_content)
    
    messages = []

    for msg in combined:
        msg_list, _ = process_message(msg)
        messages.append(msg_list)

     
    return messages
