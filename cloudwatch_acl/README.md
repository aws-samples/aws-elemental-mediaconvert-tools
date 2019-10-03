## Introduction
The following workflow allows customers running MediaConvert in Account A to put objects into Account B and will apply the `bucket-owner-full-control` ACL to all outputs. 

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
Under 'Execution role' click on the View the functionName-role-xxxx on the IAM console link. 

You will need to attach the following policy to the role that is executing the Lambda function

~~~~
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": "s3:PutObjectAcl",
            "Resource": "*"
        }
    ]
}
~~~~

What this does:
It allows the lamda function to invoke the s3:PutObjectACL call. 

#### Step 5:
Save Lamda function


 
#### Step 6: Create CloudWatch Event


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
 

 
#### Step 7: Check Logs (Optional) 
 
After running jobs complete, you should see the print output of the Lambda as CloudWatch logs
CloudWatch Logs (event name)

### Optional Infomation

The following is an example bucket policy that is used in Account B. This would allow the role configured in Account A running the MediaConvert job, to place objects in to a bucket sitting in Account B and allow the Lambda function to change object ACLs. 

~~~~
{
    "Version": "2012-10-17",
    "Id": "Policy1570060985561",
    "Statement": [
        {
            "Sid": "Stmt1570060984261",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::111122223333:role/MediaConvertRole"
            },
            "Action": [
                "s3:GetObject",
                "s3:GetObjectAcl",
                "s3:ListBucket",
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": [
                "arn:aws:s3:::bucket,
                "arn:aws:s3:::bucket/*"
            ]
        }
    ]
}
~~~~