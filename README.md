
Author: Arun Chunduru

This is to create / update the LexBot in AWS Environment. Follow the below steps,

Step-1: "aws configure" with valid credentials

Step-2: Create the following directory structure,

        /home/ec2-user/LexImport/lexImport_py36.py
        /home/ec2-user/LexConfig/Sutantra.json
        /home/ec2-user/Completed
        
Step-3: Run the python script,

        python lexImport_py36.py <<Region>>
        
        Example: python lexImport_py36.py us-east-1
        
Note:  This script will create the Slot, Intents, Alias, LexBot and Builds it.
       If you want to publish the Bot, we need to make one more Boto3 call.
       i.e. create_bot_version. It expects BOT Name and CheckSum of the Bot as
       Arguments.
       
       Checksum needs to be extracted from Bot and Bot Name can be get from the
       Variable "bot". (Check Lines 175 & 176)

   
