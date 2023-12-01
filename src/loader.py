import json
import argparse
import os
import io
import shutil
import copy
from datetime import datetime
from pick import pick
from time import sleep



# Create wrapper classes for using slack_sdk in place of slacker
class SlackDataLoader:
    '''
    n=SlackDataLoader('Data/anonymized')
    Slack exported data IO class.

    When you open slack exported ZIP file, each channel or direct message 
    will have its own folder. Each folder will contain messages from the 
    conversation, organised by date in separate JSON files.

    You'll see reference files for different kinds of conversations: 
    users.json files for all types of users that exist in the slack workspace
    channels.json files for public channels, 
    
    These files contain metadata about the conversations, including their names and IDs.

    For secruity reason, we have annonymized names - the names you will see are generated using faker library.
    
    '''
    def __init__(self, path):
        '''
        path: path to the slack exported data folder
        '''
        
        self.path = path
        self.channels = self.get_channels()
        self.users = self.get_users()
    def get_channel_sub_files(self):
        channels_files={}
        BS=r"\""[0]
        for (current_folder,folders_in_current_folder,files_in_current_folder) in os.walk(self.path):
            if(len(folders_in_current_folder) == 0):
                current_channel_name=str(current_folder).split(BS)[1]
                channels_files[current_channel_name]=files_in_current_folder
        return json.dumps(channels_files)




    def get_users(self):
        '''
        write a function to get all the users from the json file
        '''
        with open(os.path.join(self.path, 'users.json'), 'r') as f:
            users = json.load(f)

        return users
    
    def get_channels(self):
        '''
        write a function to get all the channels from the json file
        '''
        

        with open(os.path.join(self.path, 'channels.json'), 'r') as f:
            channels = json.load(f)

        return channels
    def get_channel_sub_file(self,channel_name):
        channel_sub_files=json.loads(self.get_channel_sub_files())
        return channel_sub_files[channel_name]
    def get_channel_messages_by_day(self,current_day_path):
        with open(current_day_path,'r') as f:
            message=json.load(f)
        return message
    def get_channel_messages(self, channel_name):
        channel_path=os.path.join(self.path,channel_name)
        '''
        write a function to get all the messages from a channel
        
        '''
        message={}
        daily_channel_messages_file=self.get_channel_sub_file(channel_name)
        for current_day in daily_channel_messages_file:
            current_day_path=os.path.join(channel_path,current_day)
            message[current_day]=(self.get_channel_messages_by_day(current_day_path))
        #to see if the json object is correct write into file 
        #  with open("sample.json", "w") as outfile:
        #     outfile.write(json.dumps(message))
        return json.dumps(message)
        

    

     
    def get_user_map(self):
        '''
        write a function to get a map between user id and user name
        '''
        userNamesById = {}
        userIdsByName = {}
        for user in self.users:
            userNamesById[user['id']] = user['name']
            userIdsByName[user['name']] = user['id']
        return userNamesById, userIdsByName        




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export Slack history')

    
    parser.add_argument('--zip', help="Name of a zip file to import")
    args = parser.parse_args()
