# MediaConvert Resource Cloner

This script will clone MediaConvert resources from one region to another. Users have the option to save resource configuration directly  to JSON or to import resources across regions. 

## Assumptions

The Python modules boto3 and awscli is installed. "aws configure" was run to define the access key and secret access key to be used by boto3 to interact with the MediaConvert. The user that runs the script has an IAM policy that allows the user to run list, describe and create commands with MediaConvert. 


## Execution of python script

The script has a comprehensive help function that can be accessed by the command line option “-h” or “–help”, e.g.

```
python clone_mediaconvert_resources.py -h 

Parameters
-i, --initialize:   Run to create region endpoint configuration file.
                    Run this option with no other parameters
-r, --region:       Region you would like to clone from.
-a, --action:       Individual actions allowed to clone between regions.
                    Valid options are:
                    PRESETS - Will clone all non-system job presets
                    QUEUES - Will clone all On-Demand Queues
                    TEMPLATES - Will clone all non-system job templates
                    ALL - Will clone all presets, templates, and on-demand queues
-c, --clone:        Region you would like to clone to
-f, --file:         Saves preset, templates, and queue parameters to individual files.
                    This will not clone to another region.
-h, --help:         Print this help and exit
```


In order to run this script you must have a list of MediaConvert endpoints. Run the "-i" or "--initialize" to create configuration file for endpoints to desired regions. 

```python clone_mediaconvert_resources.py-i ```

Using a clone from region of us-east-1, action of All, and clone to region of us-west-2. 

```python clone_mediaconvert_resources.py  -r us-east-1 -a ALL -c us-west-2```



