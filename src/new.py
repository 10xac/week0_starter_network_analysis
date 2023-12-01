from loader import SlackDataLoader 
import json
data_loader = SlackDataLoader('Data/anonymized')

# print(data_loader.get_channel_sub_files())
(data_loader.get_channel_messages("week-11-group4"))







# # slack_data = data_loader.get_users()
# cha=data_loader.get_channels()[0]['name']
# data_loader.get_channel_messages(cha)
# import os
# import json
# folder_path="Data/anonymized"
# # print(folder_path)

# channels_files={}
# for (current_folder,folders_in_current_folder,files_in_current_folder) in os.walk(folder_path):
#     if(len(folders_in_current_folder) == 0):
#         BS=r"\""[0]
#         # print("=======================================")
#         # print(f'*****current_folder {str(current_folder).split(BS)[1]}')
#         # print(f'*****folders_in_current_folder {str(folders_in_current_folder)}')
#         # print(f'*****files_in_current_folder {str(files_in_current_folder)}')
#         # print("=======================================")
#         current_channel=str(current_folder).split(BS)[1]
#         # channels_files[current_channel]={}
#         channels_files[current_channel]=files_in_current_folder
#         # print(current_channel)


# # print(json.loads(channels_files))
# obj = json.dumps(channels_files)
# print(obj)