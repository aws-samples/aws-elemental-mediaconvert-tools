## Amazon CloudWatch widgets for AWS Elemental MediaConvert

This document goes over how to edit  the provided Cloudwatch widgets from the blog post [Creating dashboards and alarms for AWS Elemental MediaConvert using Amazon CloudWatch](https://aws.amazon.com/blogs/media/creating-dashboards-and-alarms-for-aws-elemental-mediaconvert-using-amazon-cloudwatch/).

## Setup

Download the JSONs from github repo
Open the JSONs in a text editor of your choice. 
Change all references of the Queue ARNS to ones that are in your account.
Change all referneces of the region (us-west-2), to the desired region of your workflow.  


## Importing into CloudWatch

Click on the dashboard you wish to add the widget too
Click on Actions and then Edit/View source.
Paste the widget JSON into the widgets array object.


## Resources 
[Creating dashboards and alarms for AWS Elemental MediaConvert using Amazon CloudWatch](https://aws.amazon.com/blogs/media/creating-dashboards-and-alarms-for-aws-elemental-mediaconvert-using-amazon-cloudwatch/).

[Listing and viewing on-demand queues in AWS Elemental MediaConvert](https://docs.aws.amazon.com/mediaconvert/latest/ug/listing-queues.html)
