import json
import boto3
s3 = boto3.resource('s3')

## Pull your specific MediaConvert endpoint https://docs.aws.amazon.com/mediaconvert/latest/apireference/aws-cli.html

mediaconvert_client = boto3.client('mediaconvert', endpoint_url='https://abc1234.mediaconvert.us-west-2.amazonaws.com')


def getIVSManifest(bucket_name, prefix_name):
    object_path = "{}/events/recording-ended.json".format(prefix_name)
    object = s3.Object(bucket_name, object_path)
    body = str(object.get()['Body'].read().decode('utf-8'))
    metadata = json.loads(body)
    media_path = metadata["media"]["hls"]["path"]
    main_manifest = bucket_name + "/" + prefix_name +  "/" + media_path + '/' +metadata["media"]["hls"]["playlist"]
    print(main_manifest)
    return main_manifest
    
def createMediaConvertJob(manifest):
    ##Note change the following variables to your own, 
    role_arn = "arn:aws:iam::111122223333:role/service-role/MediaConvert_Default_Role"
    preroll_path = "s3://DOC-EXAMPLE-BUCKET/preroll.mp4"
    postroll_path = "s3://DOC-EXAMPLE-BUCKET/preroll.mp4"
    previously_recorded_image = "s3://DOC-EXAMPLE-BUCKET/previously_recorded_image.png"
    job_template = "IVS-EMC-Demo"

    
    #### No edits needed past this point 
    
    settings_json = """{
   "Inputs": [
      {
 
        "TimecodeSource": "ZEROBASED",
        "VideoSelector": {
          "ColorSpace": "FOLLOW",
          "Rotate": "DEGREE_0",
          "AlphaBehavior": "DISCARD"
        },
        "AudioSelectors": {
          "Audio Selector 1": {
            "Offset": 0,
            "DefaultSelection": "DEFAULT",
            "ProgramSelection": 1
          }
        },
        "FileInput": "%s"
      },
      {
        "TimecodeSource": "ZEROBASED",
        "VideoSelector": {
          "ColorSpace": "FOLLOW",
          "Rotate": "DEGREE_0",
          "AlphaBehavior": "DISCARD"
        },
        "AudioSelectors": {
          "Audio Selector 1": {
            "Offset": 0,
            "DefaultSelection": "DEFAULT",
            "ProgramSelection": 1
          }
        },
        "FileInput": "s3://%s",
        "ImageInserter": {
          "InsertableImages": [
            {
              "Opacity": 75,
              "ImageInserterInput": "%s",
              "Layer": 0,
              "ImageX": 0,
              "ImageY": 0,
              "FadeIn": 5000,
              "FadeOut": 5000
            }
          ]
        }
      },
      {
        "TimecodeSource": "ZEROBASED",
        "VideoSelector": {
          "ColorSpace": "FOLLOW",
          "Rotate": "DEGREE_0",
          "AlphaBehavior": "DISCARD"
        },
        "AudioSelectors": {
          "Audio Selector 1": {
            "Offset": 0,
            "DefaultSelection": "DEFAULT",
            "ProgramSelection": 1
          }
        },
        "FileInput": "%s"
      }
    ]}""" % (preroll_path,manifest,previously_recorded_image,postroll_path)
    
    response = mediaconvert_client.create_job(JobTemplate=job_template,Role=role_arn,Settings=json.loads(settings_json))
    print(response)

def lambda_handler(event, context):
    print(json.dumps(event))
    prefix_name = event["detail"]["recording_s3_key_prefix"]
    bucket_name = event["detail"]["recording_s3_bucket_name"]

    #Get path to recording_ended.json and then create a MediaConvert job 
    createMediaConvertJob(getIVSManifest(bucket_name, prefix_name))

    return {
        'statusCode': 200,
        'body': ("Job created")
    }
    