## Introduction
The following workflow allows customers running MediaConvert in Account A to put objects into Account B and will apply the bucket-owner-full-control ACL to all outputs. 

### Setup

#### Step 1: 
Create Amazon Lambda function with Python 2.7 Runtime

 
#### Step 2: 
Use the lambda_handle.py as the function code.

This will parse MediaConvert outputs and apply bucket-owner-full-control ACL to all outputs
 
#### Step 3: 
Under Basic settings, set for 1024 MB memory and 15 min timeout

**Note:** It takes about 200ms to set the ACL on each object. 
 
#### Step 4:
Save Lamnda function
 
#### Step 5: Create CloudWatch Event


+ CloudWatch -> Events -> Rules -> Create Rule
+ Set “Event Pattern” sources with:
	- MediaConvert
	- MediaConvert Job State Change
	- Specific state(s)
	- Complete
+ Set “Targets” with
	- Lambda function
	- (function name)
+ Name rule
+ Create rule

The event pattern preview will look like the following

~~~~
{
  "source": [
    "aws.mediaconvert"
  ],
  "detail-type": [
    "MediaConvert Job State Change"
  ],
  "detail": {
    "status": [
      "COMPLETE"
    ]
  }
} 
~~~~
 

 
#### Step 6: Check Logs (Optional) 
 
After running jobs complete, you should see the print output of the Lambda as CloudWatch logs
CloudWatch Logs (event name)

