import json
import boto3
import botocore
import sys
import getopt
import os
import shutil
import time

version = '0.1'
supported_regions = ["us-east-1", "us-east-2", "us-west-1", "us-west-2", "ap-south-1", "ap-northeast-2",
                     "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ca-central-1", "eu-west-1", "eu-central-1",
                     "eu-west-2", "eu-west-3", "eu-north-1", "sa-east-1"]
support_actions = ["PRESETS", "QUEUES", "TEMPLATES", "ALL"]


# General functions


def usage(app_name):
    """Function that prints out a detailed help page for the script"""
    global version
    print('\npython {0} -r REGION -a OPTION -c REGION\n'.format(app_name))
    print('Version:', version)
    print("")
    print("Parameters")
    print("-i, --initialize:   Run to create region endpoint configuration file.")
    print("                    Run this option with no other parameters")
    print("-r, --region:       Region you would like to clone from.")
    print("-a, --action:       Individual actions allowed to clone between regions.")
    print("                    Valid options are:")
    print("                    PRESETS - Will clone all non-system job presets")
    print("                    QUEUES - Will clone all On-Demand Queues")
    print("                    TEMPLATES - Will clone all non-system job templates")
    print("                    ALL - Will clone all presets, templates, and on-demand queues")
    print("-c, --clone:        Region you would like to clone to")
    print("-f, --file:         Saves preset, templates, and queue parameters to individual files. ")
    print("                    This will not clone to another region. ")
    print("-h, --help:         Print this help and exit.")
    print("")
    print('Important Notes:')
    print("")
    print("You must run -i option first in order to create your endpoint configuration file")
    print("You can run -i again to add more regions as needed")
    print("")
    print("If you are using the individual options to clone resources (ie: not the ALL option), the order ")
    print("of operations should be Presets, Queues and then Templates. This will insure that all dependencies are ")
    print("in place before cloning job templates. ")
    print("")
    print('Examples:')
    print("")
    print("Creates MediaConvert endpoints configuration file")
    print("python {0} -i".format(app_name))
    print("")
    print("Using a clone from region of us-east-1, action of All, and clone to region of us-west-2")
    print("python {0} -r us-east-1 -a ALL -c us-west-2".format(app_name))
    print("")
    print("Using a clone from region of us-east-1, action of Presets, and saving to file as eu-west-1 resources")
    print("python {0} -r us-east-1 -c eu-west-1 -a PRESET -f".format(app_name))


def print_mini_help(app_name):
    """Print statement showing how to use the '-h/--help' option to get help on proper usage of the script"""
    print("\nExecute the script with either '-h' or '--help' to obtain detailed help on how to run the script:")
    print('python {0} -h'.format(app_name))
    print("or")
    print('python {0} --help\n'.format(app_name))


def is_valid_supported_region(region):
    return region in supported_regions


def is_valid_config_region(region):
    config_regions = []
    try:
        with open('mediaconvertcloner.config.json') as endpoints:
            data = json.load(endpoints)
        for k, v in data.items():
            config_regions.append(k)
        return region in config_regions
    except FileNotFoundError:
        print("No configuration file found, please run script with -i")
        exit()


def is_valid_action(action):
    return action in support_actions


def create_directory(option):
    cwd = os.getcwd()
    path = os.path.join(cwd, option)
    os.mkdir(path)


def get_presets(source_client, file):
    try:
        response = source_client.list_presets(ListBy='NAME')
        results = response['Presets']

        while "NextToken" in response:
            response = source_client.list_presets(NextToken=response["NextToken"])
            results.extend(response["Presets"])
        if len(results) == 0:
            return
        else:
            path = clean_presets(results, file)
            return path
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'AccessDeniedException':
            print("No Permissions to access the MediaConvert API and get output presets,"
                  " please check the AWS CLI credentials")
            exit(-1)
    except:
        print("Error processing preset resources in source region")


def clean_presets(dirty_presets, file):
    try:
        clean_presets = []
        resource_arns = []
        for preset in dirty_presets:
            new_preset_struct = {'Name': preset['Name'], 'Settings': preset['Settings'], 'Category': '',
                                 'Description': ''}
            if 'Category' in preset:
                new_preset_struct['Category'] = preset['Category']

            if 'Description' in preset:
                new_preset_struct['Description'] = preset['Description']

            clean_presets.append(new_preset_struct)
            resource_arns.append(preset['Arn'])

        get_resource_tags(resource_arns, file)

        if file == "single":
            if not os.path.exists('presets'):
                create_directory("presets")

            with open('presets/list.json', 'w') as output_file:
                json.dump(clean_presets, output_file)
            return 'presets/list.json'
        else:
            t = time.time()
            working_directory = "presets_" + str(int(t))
            create_directory(working_directory)

            for c_preset in clean_presets:
                filename = c_preset['Name'] + ".json"
                with open(working_directory + '/' + filename, 'w+') as output_file:
                    json.dump(c_preset, output_file)
            return working_directory
    except:
        print("Error: Unknown Error when trying to create preset file")
        shutil.rmtree("presets")
        exit(-1)


def create_presets(destination_client, presets_file):
    with open(presets_file) as presets:
        preset_data = json.load(presets)
    try:
        for preset in preset_data:
            response = destination_client.create_preset(
                Name=preset['Name'],
                Settings=preset['Settings'],
                Category=preset['Category'],
                Description=preset['Description']
            )
        account_id = response['Preset']['Arn'].split('/')[0].split(":")[4]
        resource_type = response['Preset']['Arn'].split('/')[0].split(":")[5]
        create_resource_tags(destination_client, account_id, resource_type)
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'BadRequestException':
            print("Problem processing preset name:" + preset['Name'])
        elif error.response['Error']['Code'] == 'ParamValidationError':
            print("Problem processing preset name:" + preset['Name'])
            print("Boto3 is out of date, please upgrade boto3 library on this machine")
        elif error.response['Error']['Code'] == 'TooManyRequestsException':
            print("Number of presets allowed exceeded, please open a service quota request")
        elif error.response['Error']['Code'] == 'AccessDeniedException':
            print("No Permissions to access the MediaConvert API and create output presets,"
                  " please check the AWS CLI credentials")
            exit(-1)


def get_queues(source_client, file):
    try:
        response = source_client.list_queues(ListBy='NAME')
        results = response['Queues']
        while "NextToken" in response:
            response = source_client.list_queues(NextToken=response["NextToken"])
            results.extend(response["Queues"])

        # Check to see if there is only 1 queue:
        if len(results) == 1:
            print("You only have 1 queue, which is the Default queue, in the region. ")
            print("All MediaConvert regions come with an Default queue, there is no need to clone this ")
            return
        else:
            path = clean_queues(results, file)
            return path
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'AccessDeniedException':
            print("No permissions to access the MediaConvert API and get queues,"
                  " please check the AWS CLI credentials")
            exit(-1)
    except:
        print("Error processing queue resources in source region")


def get_resource_tags(arns, file):
    try:
        region = arns[0].split('/')[0].split(':')[3]
        resource_client = create_clients(region)
        tagged_resource = []
        for arn in arns:
            results = resource_client.list_tags_for_resource(Arn=arn)
            if results['ResourceTags']['Tags'] != {}:
                tagged_resource.append(results['ResourceTags'])

        if len(tagged_resource) > 0:
            clean_resource_tags(tagged_resource, file)
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'AccessDeniedException':
            print("No permissions to access the MediaConvert API and get resource tags,"
                  " please check the AWS CLI credentials")
            exit(-1)


def clean_resource_tags(arns, file):
    resource_type = arns[0]['Arn'].split('/')[0].split(":")[5]
    clean_tags = []
    for arn in arns:
        resource_name = arn['Arn'].split('/')[1]
        tags = {}
        for k, v in arn['Tags'].items():
            tags[k] = v
        clean_tags.append({resource_name: tags})
    if file == "single":
        if not os.path.exists(resource_type):
            create_directory(resource_type)

        file_path = resource_type + "/resource.json"
        with open(file_path, 'w') as output_file:
            json.dump(clean_tags, output_file)

    else:

        t = time.time()
        working_directory = resource_type + "_resource_tags_" + str(int(t))
        create_directory(working_directory)

        for c_tags in clean_tags:
            for tag in c_tags:
                filename = tag + ".json"
                with open(working_directory + '/resource_tag_' + filename, 'w+') as output_file:
                    json.dump(c_tags, output_file)


def clean_queues(dirty_queues, file):
    try:
        clean_queues = []
        resource_arns = []

        for queue in dirty_queues:

            # Check for On-Demand Queue since we only support migrating those and no Default queues
            if queue['PricingPlan'] == 'ON_DEMAND' and queue['Name'] != 'Default':
                clean_queues_struct = {'Name': queue['Name'], 'Description': ''}
                if 'Category' in queue:
                    clean_queues_struct['Category'] = queue['Category']

                if 'Description' in queue:
                    clean_queues_struct['Description'] = queue['Description']

                clean_queues.append(clean_queues_struct)
                resource_arns.append(queue['Arn'])

        get_resource_tags(resource_arns, file)

        if file == "single":
            if not os.path.exists('queues'):
                create_directory("queues")

            with open('queues/list.json', 'w') as output_file:
                json.dump(clean_queues, output_file)
            return 'queues/list.json'
        else:
            t = time.time()
            working_directory = "queue_" + str(int(t))
            create_directory(working_directory)

            for c_queues in clean_queues:
                filename = c_queues['Name'] + ".json"
                with open(working_directory + '/' + filename, 'w+') as output_file:
                    json.dump(c_queues, output_file)
            return working_directory
    except:
        print("Error: Unknown Error when trying to create queue file")
        shutil.rmtree("queues")
        exit(-1)


def create_queues(destination_client, queue_file):
    with open(queue_file) as queues:
        queue_data = json.load(queues)
    try:
        for queue in queue_data:
            response = destination_client.create_queue(
                Name=queue['Name'],
                Description=queue['Description']
            )
        account_id = response['Queue']['Arn'].split('/')[0].split(":")[4]
        resource_type = response['Queue']['Arn'].split('/')[0].split(":")[5]
        create_resource_tags(destination_client, account_id, resource_type)

    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'TooManyRequestsException':
            print("Number of queue allowed exceeded, please open a service quota request")
        elif error.response['Error']['Code'] == 'AccessDeniedException':
            print("No permissions to access the MediaConvert API and create queues,"
                  " please check the AWS CLI credentials")
            exit(-1)


def create_resource_tags(destination_client, account, resource_type):
    try:
        region = destination_client.meta.region_name
        resource_data = []
        item = []
        file_path = resource_type + "/resource.json"
        file_path_bool = os.path.isfile((os.path.exists(file_path)))
        if file_path_bool == True:

            with open(file_path) as resources:
                resource_data = json.load(resources)

            for item in resource_data:
                for resource in item:
                    arn = "arn:aws:mediaconvert:" + region + ":" + account + ":" + resource_type + "/" + resource
                    destination_client.tag_resource(
                        Arn=arn,
                        Tags=item[resource]
                    )

        # else nothing to do because we have no resources to tag
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'AccessDeniedException':
            print("No permissions to access the MediaConvert API and tag resources,"
                  " please check the AWS CLI credentials")
            exit(-1)


def get_templates(source_client, file, region):

    try:
        response = source_client.list_job_templates(ListBy='NAME')
        results = response['JobTemplates']
        while "NextToken" in response:
            response = source_client.list_job_templates(NextToken=response["NextToken"])
            results.extend(response["JobTemplates"])

        if len(results) == 0:
            return
        else:
            path = clean_templates(results, file, region)
            return path
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'AccessDeniedException':
            print("No permissions to access the MediaConvert API and get job templates,"
                  " please check the AWS CLI credentials")
            exit(-1)
    except:
        print("Error processing job template resources in source region")
        exit(-1)


def clean_templates(dirty_templates, file, region):
    try:
        clean_templates = []
        resource_arns = []
        for template in dirty_templates:
            new_template_struct = {'Name': template['Name'], 'Settings': template['Settings'], 'Category': '',
                                   'Description': '', 'Queue': '', 'Priority': 0,
                                   'AccelerationSettings': {'Mode': 'DISABLED'}, 'StatusUpdateInterval': 'SECONDS_60',
                                   'HopDestinations': []}
            if 'Category' in template:
                new_template_struct['Category'] = template['Category']

            if 'Description' in template:
                new_template_struct['Description'] = template['Description']

            if 'Priority' in template:
                new_template_struct['Priority'] = int(template['Priority'])

            if 'AccelerationSettings' in template:
                new_template_struct['AccelerationSettings']['Mode'] = template['AccelerationSettings']['Mode']

            if 'Queue' in template:
                new_queue_name = template['Queue'].split('/')[1]
                account_number = template['Queue'].split(':')[4]
                new_queue = 'arn:aws:mediaconvert:' + region + ':' + account_number + ':queues/' + new_queue_name
                new_template_struct['Queue'] = new_queue

            if 'StatusUpdateInterval' in template:
                new_template_struct['StatusUpdateInterval'] = template['StatusUpdateInterval']

            if 'HopDestinations' in template:

                for hop_queue in template['HopDestinations']:
                    new_hop_queue_name = hop_queue['Queue'].split('/')[1]
                    account_number = hop_queue['Queue'].split(':')[4]
                    new_hop_queue = 'arn:aws:mediaconvert:' + region + ':' + account_number + \
                                    ':queues/' + new_hop_queue_name
                    new_hop_destination = {'Queue': new_hop_queue, 'Priority': hop_queue['Priority'], 'WaitMinutes':
                        hop_queue['WaitMinutes']}
                    new_template_struct['HopDestinations'].append(new_hop_destination)

            clean_templates.append(new_template_struct)
            resource_arns.append(template['Arn'])

        get_resource_tags(resource_arns, file)

        if file == "single":
            if not os.path.exists('jobTemplates'):
                create_directory("jobTemplates")
            with open('jobTemplates/list.json', 'w') as output_file:
                json.dump(clean_templates, output_file)
            return 'jobTemplates/list.json'
        else:
            t = time.time()
            working_directory = "templates_" + str(int(t))
            create_directory(working_directory)

            for c_template in clean_templates:
                filename = c_template['Name'] + ".json"
                with open(working_directory + '/' + filename, 'w+') as output_file:
                    json.dump(c_template, output_file)
            return working_directory
    except:
        print("Error: Unknown Error when trying to create template file")
        shutil.rmtree("jobTemplates")
        exit(-1)


def create_templates(destination_client, template_file):
    with open(template_file) as template:
        template_data = json.load(template)
    try:
        for template in template_data:
            response = destination_client.create_job_template(
                Name=template['Name'],
                Settings=template['Settings'],
                Category=template['Category'],
                Description=template['Description'],
                Queue=template['Queue'],
                AccelerationSettings=template['AccelerationSettings'],
                Priority=template['Priority'],
                StatusUpdateInterval=template['StatusUpdateInterval'],
                HopDestinations=template['HopDestinations']
            )
        account_id = response['JobTemplate']['Arn'].split('/')[0].split(":")[4]
        resource_type = "jobTemplates"
        create_resource_tags(destination_client, account_id, resource_type)

    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'BadRequestException':
            print("Problem processing job template name:" + template['Name'])
        elif error.response['Error']['Code'] == 'ParamValidationError':
            print("Problem processing job template name:" + template['Name'])
            print("Boto3 is out of date, please upgrade boto3 library on this machine")
        elif error.response['Error']['Code'] == 'TooManyRequestsException':
            print("Number of job templates  allowed exceeded, please open a service quota request")
        elif error.response['Error']['Code'] == 'NotFoundException':
            print(error)
            print("Make sure to import your output presets and queues before cloning job templates")
        elif error.response['Error']['Code'] == 'AccessDeniedException':
            print("No permissions to access the MediaConvert API and create job templates,"
                  " please check the AWS CLI credentials")
            exit(-1)


def create_clients(region):
    try:
        endpoint = read_endpoint(region)
        client = boto3.client("mediaconvert", region_name=region, endpoint_url=endpoint)
        return client
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'AccessDeniedException':
            print("No permissions to access the MediaConvert API and get endpoints"
                  ", please check the AWS CLI credentials")
            exit(-1)


def read_endpoint(region):
    with open('mediaconvertcloner.config.json') as endpoints:
        data = json.load(endpoints)
    return data[region]


def get_endpoint(region):
    # Create Client request to get endpoint
    try:
        mediaconvert_subscribe = boto3.client("mediaconvert", region_name=region)
        endpoint = mediaconvert_subscribe.describe_endpoints()
        return endpoint['Endpoints'][0]['Url']
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'AccessDeniedException':
            print("No permissions to access the MediaConvert API and get endpoints"
                  ", please check the AWS CLI credentials")
            exit(-1)


def clone(source, destination, action):
    source_client = create_clients(source)
    destination_client = create_clients(destination)
    try:
        if action == 'PRESETS':
            print("Processing Presets")
            presets = get_presets(source_client, "single")
            if presets is not None:
                create_presets(destination_client, presets)
                print("Presets imported to " + destination)
            else:
                print("No presets to clone")

        elif action == 'QUEUES':
            print("Processing Queues ")
            queues = get_queues(source_client, "single")
            if queues is not None:
                create_queues(destination_client, queues)
                print("Queues imported to " + destination)
            else:
                print("No queues to clone")
        elif action == 'TEMPLATES':
            print("Processing Job Templates")
            templates = get_templates(source_client, "single", destination)
            if templates is not None:
                create_templates(destination_client, templates)
                print("Job Templates imported to " + destination)
            else:
                print("No job templates to clone")
        elif action == 'ALL':
            print("Processing ALL resources")
            print("Processing Queues ")
            queues = get_queues(source_client, "single")
            if queues is not None:
                create_queues(destination_client, queues)
                print("Queues imported to " + destination)
            else:
                print("No queues to clone")

            print("Processing Presets")
            presets = get_presets(source_client, "single")
            if presets is not None:
                create_presets(destination_client, presets)
                print("Presets imported to " + destination)
            else:
                print("No presets to clone")

            print("Processing Job Templates")
            templates = get_templates(source_client, "single", destination)
            if templates is not None:
                create_templates(destination_client, templates)
                print("Job Templates imported to " + destination)
            else:
                print("No job templates to clone")
    finally:
        if os.path.exists("queues"):
            shutil.rmtree("queues")
        if os.path.exists("presets"):
            shutil.rmtree("presets")
        if os.path.exists("jobTemplates"):
            shutil.rmtree("jobTemplates")


def save_to_file(source, destination, action):
    source_client = create_clients(source)
    if action == 'PRESETS':
        print("Processing Presets")
        presets = get_presets(source_client, "multi")
        print("Saved Presets to " + presets + " directory")
        exit()
    elif action == 'QUEUES':
        print("Processing Queues")
        queues = get_queues(source_client, "multi")
        print("Saved Queues to " + queues + " directory")
        exit()
    elif action == 'TEMPLATES':
        print("Processing Job Templates")
        template = get_templates(source_client, "multi", destination)
        print("Saved Job Templates to " + template + " directory")
    elif action == 'ALL':
        print("Processing ALL resources")
        print("Processing Queues ")
        queues = get_queues(source_client, "multi")
        if queues is not None:
            print("Saved Queues to " + queues + " directory")
        else:
            print("No queues to clone")

        print("Processing Presets")
        presets = get_presets(source_client, "multi")
        if presets is not None:
            print("Saved Presets to " + presets + " directory")
        else:
            print("No presets to clone")

        print("Processing Job Templates")
        templates = get_templates(source_client, "multi", destination)
        if templates is not None:
            print("Saved Job Templates to " + templates + " directory")
        else:
            print("No job templates to clone")


def check_config():
    try:
        regions = []
        with open('mediaconvertcloner.config.json') as endpoints:
            data = json.load(endpoints)
        for k, v in data.items():
            regions.append(k)
        answer = input(
            "Found endpoints for the following regions: \n" + repr(regions) + "\n Would you like to add more? [Y/N]")
        check = input_is_valid(answer)
        while check is False:
            print("Incorrect option. Please use Y or N")
            answer = input("Found endpoints for the following regions: \n" + repr(
                regions) + "\n Would you like to add more? [Y/N]")
            print(answer)
            check = input_is_valid(answer)

        if answer == 'Y':
            more_regions = user_question_config(regions)
            for k, v in more_regions.items():
                data[k] = v

        print("Saving configuration file...")
        with open('mediaconvertcloner.config.json', 'w') as output_file:
            json.dump(data, output_file)
    except:
        print("Error loading mediaconvertcloner.config.json. Renaming config. Please rerun script with "
              "-i to re-initialize")
        os.rename(r'mediaconvertcloner.config.json', 'mediaconvertcloner.config.json.error')
        exit(-1)


def input_is_valid(input):
    if input.upper() == "Y" or input.upper() == "N" or input.upper() == "Q":
        return True
    else:
        return False


def user_question_config(added_regions):
    data = {}

    # remove items from list before processing

    if added_regions is not None:
        for region in added_regions:
            supported_regions.remove(region)

    for region in supported_regions:
        answer = input("Would you like to add support for the " + region + " region? [Y/N/Q]")
        print(answer)
        check = input_is_valid(answer)
        while check is False:
            print("Incorrect option. Please use Y, N, or Q")
            answer = input("Would you like to add support for the " + region + " region? [Y/N/Q]")
            print(answer)
            check = input_is_valid(answer)

        if answer.upper() == 'Y':
            endpoint = str(get_endpoint(region))
            data[region] = endpoint
        elif answer.upper() == 'Q':
            break

    return data


def create_config():
    print("Creating mediaconvertcloner.config.json . \n Please provide regions you would like to clone to and from. Use"
          " Q to exit out of the prompts")
    data = user_question_config(None)

    if data == {}:
        print('No regions added, exiting')
        exit(-1)
    # Write config
    with open('mediaconvertcloner.config.json', 'w+') as output_file:
        json.dump(data, output_file)


def main(argv=None):
    initialize = False
    save_file = False
    clone_region_used = False
    destination_region = None
    source_region = None
    action = None

    # check opt
    if initialize:
        if not os.path.exists('mediaconvertcloner.config.json'):
            print("No configuration file found please run the script with -i before cloning")
            exit(-1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hic:r:a:f', ['help', 'initialize', 'clone=', 'region=', 'action=',
                                                               'file'])
    except getopt.GetoptError as err:
        print(str(err))
        usage(sys.argv[0])
        exit(-1)

    if len(sys.argv) == 1:
        usage(sys.argv[0])
        exit()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(sys.argv[0])
            sys.exit(0)
        elif opt in ("-r", "--region"):
            if is_valid_supported_region(arg):
                if is_valid_config_region(arg):
                    source_region = arg
                else:
                    print("Invalid region parameter: Specified region was not found in the configuration "
                          "file. Re-run the script with -i")
                    exit(-1)
            else:
                print("Invalid region parameter: Not a supported MediaConvert Region")
                exit(-1)
        elif opt in ("-a", "--action"):
            if is_valid_action(arg):
                action = arg
            else:
                print("Invalid action parameter: Not a supported action")
                exit(-1)
        elif opt in ("-c", "--clone"):
            if is_valid_supported_region(arg):
                if is_valid_config_region(arg):
                    destination_region = arg
                else:
                    print("Invalid clone parameter: Specified region was not found in the configuration file. "
                          "Re-run the script with -i")
                    exit(-1)
            else:
                print("Invalid clone parameter: Not a supported MediaConvert Region")
                exit(-1)
            clone_region_used = True
        elif opt in ("-f", "--file"):
            save_file = True
        elif opt in ("-i", "--initialize"):
            initialize = True
        else:
            assert False, "Unhandled option '{0}'".format(opt)

    if initialize:
        if os.path.exists('mediaconvertcloner.config.json'):
            check_config()
            exit()
        else:
            create_config()
            exit()


    if source_region == destination_region:
        print("Error: Source region and clone region are the same")
        exit(-1)

    if save_file:
        save_to_file(source_region, destination_region, action)
    else:
        clone(source_region, destination_region, action)


if __name__ == '__main__':
    sys.exit(main())

# TODO create helper function for parsing arn
