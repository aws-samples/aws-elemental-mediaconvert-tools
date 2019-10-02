# ---------------------------------------------------------------------------
# AWS Elemental MedaConvert Cloudwatch ACL Object Changer 
# Version: 1.0
#
# 1.0 Initial commit
#
#
# Known Issues:
#
# Audio Only outputs ACL's do not change
# 
#
# ---------------------------------------------------------------------------

import json
import boto3

def lambda_handler(event, context):
    print(event)

    for outputGroupDetails in event['detail']['outputGroupDetails']:
        
        #File Groups
        for outputDetails in outputGroupDetails['outputDetails']:
            if 'outputFilePaths' in outputDetails:
                for outputFilePath in outputDetails['outputFilePaths']:
                    setACL( getBucket(outputFilePath), getKey(outputFilePath) )
                
        #ABR Packages
        if 'playlistFilePaths' in outputGroupDetails:
            processedKeys = []
            for playlistFilePath in outputGroupDetails['playlistFilePaths']:    
                print("Setting ACLs on objects related to " + playlistFilePath)
                baseKey = getKey(playlistFilePath).split(".")[-2]
                for variant in boto3.resource('s3').Bucket(getBucket(playlistFilePath)).objects.filter(Prefix=baseKey):
                    if (variant.key not in processedKeys):
                        setACL(getBucket(playlistFilePath), variant.key)
                        processedKeys.append(variant.key)
                    else:
                        skip(getBucket(playlistFilePath), variant.key)
                    
                
def setACL (bucket, key):
    print ('Setting bucket-owner-full-control on "' + key + '" in "' + bucket + '"')
    boto3.resource('s3').ObjectAcl(bucket, key).put(ACL='bucket-owner-full-control')

def skip (bucket, key):
    print ('Skipping "' + key + '" in "' + bucket + '", ACL already set')
    
def getBucket (s3Url):
    return s3Url.split("/")[2]
    
def getKey (s3Url):
    key = s3Url.split(getBucket(s3Url))[1]
    key = key[1:]
    return key
