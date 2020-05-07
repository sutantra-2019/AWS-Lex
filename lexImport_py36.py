"""
Created on Thu Jan 31 11:38:32 2019

@author: ChunduruA
"""

from subprocess import PIPE
from zipfile import ZipFile

import boto3, json, sys, subprocess, os, shutil, pickle, datetime, time

dt = str(datetime.datetime.now())[0:19].replace('-','').replace(':','').replace(' ','')

try:
    region = sys.argv[1]
except IndexError:
    print ("===> The first argument is Region, Which is mandatory !!! Please enter region ...")
    sys.exit()

try:
    LexObj = sys.argv[2]
except IndexError:
    print ("===>  Expecting Input Argument As INTENT or BOT, Which Is Not Fount.. So Defaulting to BOT !!!!")
    LexObj = "BOT"

LexBot  = boto3.client('lex-models', region_name=region)

print ("------------------------------------------------------------------------------------------------------")
print (" ---> Getting The File Information From $Root/LexImport/LexConfig Folder And Zip Configuration JSON")
print ("------------------------------------------------------------------------------------------------------")

def get_all_file_paths(directory):

    # initializing empty file paths list
    file_paths = []

    # crawling through directory and subdirectories
    for root, directories, files in os.walk(directory):
        for filename in files:
            # join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)

    # returning all file paths
    return file_paths

def main():
    # path to folder which needs to be zipped
    directory = './LexConfig'

    # calling function to get all file paths in the directory
    file_paths = get_all_file_paths(directory)

    # printing the list of file available in config folder
    print("Files Avaialble In LexConfig Folder:")
    fileCnt=0

    for file_name in file_paths:
        fileCnt += 1
        print(file_name)


    if fileCnt > 1:
        print ("===> Folder Contains More Than One Lex Configuration !!! Please Check")
        sys.exit()

    # writing files to a zipfile
    with ZipFile('./LexConfig/LexConfig.zip','w') as zip:
        # writing each file one by one
        for file in file_paths:
            zip.write(file)

    print('The Lex Configuration Zipped Successfully!')

    print ("------------------------------------------------------------------------------------------------------")
    print ("Exporting The Lex Configuration To AWS Lex")
    print ("------------------------------------------------------------------------------------------------------")

    proc = subprocess.Popen(['aws', 'lex-models', 'start-import', '--payload', 'fileb://LexConfig/LexConfig.zip', '--resource-type', LexObj, '--merge-strategy', 'OVERWRITE_LATEST'], stdout=PIPE, stderr=PIPE)

    out, err = proc.communicate()
    print (err)
    out1 = json.loads(out)
    bot = out1['name']
    env = bot.split('_')[-1]
    print ("===> Got the Environment As : "+env)
    print ("===> Bot : " + bot)
    print ("------------------------------------------------------------------------------------------------------")
    print ("Getting Bot Latest Version")
    print ("------------------------------------------------------------------------------------------------------")

    time.sleep(10)

    LexBot  = boto3.client('lex-models', region_name=region)
    botVersions = LexBot.get_bot_versions(name=bot)
    #print botVersions

    del(botVersions['ResponseMetadata'])

    class DatetimeEncoder(json.JSONEncoder):
        def default(self, obj):
            try:
                return super(DatetimeEncoder, obj).default(obj)
            except TypeError:
                return str(obj)

    botVer  = json.loads(json.dumps(botVersions, cls=DatetimeEncoder))
    #print botVer
    for ver in botVer:
        #print ver
        for ver1 in botVer[ver]:
                LatestVer = ver1
                LatestVer=str(LatestVer["version"])
                print ("Inside Of For :" + LatestVer)

    #print "Latest BOT Version Is : " + LatestVer

    try:
        get_Bot_Alias = LexBot.get_bot_alias(name=env, botName=bot)
        botAlias  = json.loads(json.dumps(get_Bot_Alias, cls=DatetimeEncoder))
        del(botAlias['ResponseMetadata'])
        botAlias_cs = botAlias['checksum']
        print ("===> Bot Alias CheckSum Is : "+ botAlias_cs)
        put_Bot_Alias = LexBot.put_bot_alias(name=env, description='Alias For The Environment', botName=bot, botVersion=LatestVer, checksum=botAlias_cs)
        print ("===> Updated The BOT Alias : "+env)
    except:
        put_Bot_Alias = LexBot.put_bot_alias(name=env, description='Alias For The Environment', botName=bot, botVersion=LatestVer)
        print ("===> Created BOT Alias : "+env)

    exitcode = proc.returncode

    if exitcode == 0:

        print ("====> Sucessfully Imported The Configuration <====")

        # path to folder which needs to be zipped
        directory = './LexConfig'

        lexOutput = open( './LexConfig/LexConfig_Import_Status.txt', 'wb' )
        pickle.dump(out,lexOutput)
        lexOutput.close()

        # calling function to get all file paths in the directory
        file_paths = get_all_file_paths(directory)

        print ("====> Moving The Files To $Root/LexImport/Completed Folder <====")
        mvDir = './Completed/'+dt
        for file_name in file_paths:
                mvFile = file_name.split('/')[-1]
                print (mvDir+"_"+mvFile)
                shutil.move(file_name, mvDir+"_"+mvFile)

        LexBot  = boto3.client('lex-models', region_name=region)

        print ("===> Building The Bot : " + bot)
        #print bot

        try:
                getBot = LexBot.get_bot(name=bot, versionOrAlias='$LATEST')
                del(getBot['ResponseMetadata'],getBot['detectSentiment'],getBot['version'],getBot['lastUpdatedDate'],getBot['createdDate'],getBot['status'])
        except:
                print ("### Bot Not Found")
                sys.exit()

        botInfo = json.dumps(getBot)

        #print(botInfo)

        proc = subprocess.Popen(['aws', 'lex-models', 'put-bot', '--region', region, '--name', bot, '--cli-input-json', botInfo], stdout=PIPE, stderr=PIPE)

        out, err = proc.communicate()
        #print (out)
        print (err)
		
		# If you want to Publish a new version after the Building the BOT, we can extract the checksum from the above "out" variable and invoke 
		# the BOTO3 method "create_bot_version" with the arguments Bot Name (You can refer the name of the bot from above and Checksum.

    else:

        print ("====> Failed On Imported The Configuration <====")

        # path to folder which needs to be zipped
        directory = './LexConfig'

        # calling function to get all file paths in the directory
        file_paths = get_all_file_paths(directory)

        print ("====> Moving The Files To $Root/LexImport/Error Folder <====")
        mvDir = './Error/'+dt
        for file_name in file_paths:
                mvFile = file_name.split('/')[-1]
                shutil.move(file_name, mvDir+"_"+mvFile)

if __name__ == "__main__":
    main()
