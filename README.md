## AWS Elemental Mediaconvert Tools

AWS Elemental MediaConvert is a service that formats and compresses offline video content for delivery to televisions or connected devices. High-quality video transcoding makes it possible to create on-demand video assets for virtually any device.

This repository contains code samples, functioning apps, as well as links to other resources that can help customers use AWS Elemental MediaConvert. 

## Directory

[MediaConvert Object ACL](https://github.com/aws-samples/aws-elemental-mediaconvert-tools/tree/master/cloudwatch_acl "MediaConvert Object ACL")

By default MediaConvert will set owner of an object to the the account that is running the actual MediaConvert job. This presents a problem if Account A (running MediaConvert) is placing outputs in a S3 bucket that resides in Account B. This Lambda function is triggered by a Cloudwatch Event that will traverse the output files from a MediaConvert job and will set the output objects ACL of that job to  `bucket-owner-full-control`


[MediaConvert CloudWatch Widgets](https://github.com/aws-samples/aws-elemental-mediaconvert-tools/tree/master/cloudwatch_metrics "MediaConvert CloudWatch Widget")

Widget templates for Amazon CloudWatch dashboards that use AWS Elemental MediaConvert metrics.  

[MediaConvert Resource Cloner](https://github.com/aws-samples/aws-elemental-mediaconvert-tools/tree/master/clone_mediaconvert_resources "MediaConvert Resource Cloner ACL")

Python script used to clone MediaConvert resources between regions 

[Postman Collections](https://github.com/aws-samples/aws-elemental-mediaconvert-tools/tree/master/postman "Postman collections")

Postman collections used to interact with the MediaConvert API

## License Summary

This sample code is made available under the MIT-0 license. See the LICENSE file.
