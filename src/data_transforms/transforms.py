#!/usr/bin/env python3

import os
import yaml
import logging
import json
import re
from pathlib import Path
from pprint import pformat

logger = logging.getLogger(__name__)

def log_raise_value_error(local_logger=logger, item=None, err=None):
    local_logger.error(err)
    if item:
        local_logger.info(pformat(item))
    raise ValueError(err)

def make_dir(file_path_name=None):
    if not file_path_name:
        log_raise_value_error(err=f"file path cannot be empty")
    p = Path(file_path_name).parent
    p.mkdir(parents=True, exist_ok=True)

def load_yaml_files(directory_path, nameKey):
    data = {}
    
    # Loop through all files in the directory
    for file in os.listdir(directory_path):
        if file.endswith(".yaml"):
            # Load YAML file into a dictionary
            with open(os.path.join(directory_path,file), 'r') as yaml_file:
                yaml_data = yaml.safe_load(yaml_file)
                
                # Add data from the YAML file to the main dictionary
                data[yaml_data[nameKey]] = yaml_data
    
    return data

def merge_variable_sets(variables, variable_sets, project_name):
    for var in variables:
        if str(variables[var]['OwnerId']).startswith("Projects-"):
            variables[var].update({"Name": "ProjectSpecificVariables_" + project_name})
        else:
            foundSet = variable_sets[variables[var]['OwnerId']]
            variables[var].update({"Name": foundSet['Name'].translate(str.maketrans({' ': '_', '-': '_', '.': '_'}))})
    return variables

def normalize_parameters(input):
    map = {}
    # We can assume that all variables are going to be overwritten by the Project Specific Variables, 
    # so let's sort our input set to process the Project Specific Variables last
    sortedkeys = sorted(input.keys())
    for set in sortedkeys:
        varSetName = input[set]["Name"]
        map.update({varSetName :{"staging":{"secrets":{}, "parameters":{}}, "production":{"secrets":{}, "parameters":{}}}})
        varset=input[set]["Variables"]
        for var in varset:
            if var["IsSensitive"]:
                varType = "secrets"
            else:
                varType = "parameters"

            if var["Scope"] == {}:
                map[varSetName]["staging"][varType].update({var["Name"]:var["Value"]})
                map[varSetName]["production"][varType].update({var["Name"]:var["Value"]})
            elif var["Scope"]["Environment"][0] == "Environments-1":
                map[varSetName]["staging"][varType].update({var["Name"]:var["Value"]})
            elif var["Scope"]["Environment"][0] == "Environments-2":
                map[varSetName]["production"][varType].update({var["Name"]:var["Value"]})
            else:
                print("ERROR: Unknown environment")
    return map

def normalize_parameters_by_type(input):
    map = {}
    # We can assume that all variables are going to be overwritten by the Project Specific Variables, 
    # so let's sort our input set to process the Project Specific Variables last
    sortedkeys = sorted(input.keys())
    for set in sortedkeys:
        varSetName = input[set]["Name"]
        map.update({varSetName :{"secrets":{"staging":{}, "production":{}}, "parameters":{"staging":{}, "production":{}}}})
        varset=input[set]["Variables"]
        for var in varset:
            if var["IsSensitive"]:
                varType = "secrets"
            else:
                varType = "parameters"

            if var["Scope"] == {}:
                map[varSetName][varType]["staging"].update({var["Name"]:var["Value"]})
                map[varSetName][varType]["production"].update({var["Name"]:var["Value"]})
            elif var["Scope"]["Environment"][0] == "Environments-1":
                map[varSetName][varType]["staging"].update({var["Name"]:var["Value"]})
            elif var["Scope"]["Environment"][0] == "Environments-2":
                map[varSetName][varType]["production"].update({var["Name"]:var["Value"]})
            else:
                print("ERROR: Unknown environment")
    return map

def write_hcl_file(file_path_name=None, content=None, project="app", environment="staging"):
    logger.info(f"writing {file_path_name} ...")
    make_dir(file_path_name=file_path_name)
    with open(file_path_name, 'w', newline='\n') as fp:
        fp.write("locals {\n  " + project + " = {\n    " + environment + " = ")
    with open(file_path_name, 'a', newline='\n') as fp:
        json.dump(dict(sorted(content.items())), fp, indent=6, separators=["", " = "])
    with open(file_path_name, 'a', newline='\n') as fp:
        fp.write("\n  }\n}\n")

def export_project_variable_mappings(file_path_name=None, content=None, project="app"):
    # map = {project: list(sorted(content.keys()))}
    make_dir(file_path_name=file_path_name)
    with open(file_path_name, 'w', newline='\n') as fp:
        fp.write("locals {\n  " + project + " = ")
    with open(file_path_name, 'a', newline='\n') as fp:
        json.dump(list(sorted(content.keys())), fp, indent=4, separators=[",", " = "])
    with open(file_path_name, 'a', newline='\n') as fp:
        fp.write("\n  }\n")

def export_comprehensive_list(file_path_name=None, content=None, project="app"):
    make_dir(file_path_name=file_path_name)
    with open(file_path_name, 'w', newline='\n') as fp:
        fp.write("locals ")
    with open(file_path_name, 'a', newline='\n') as fp:
        # json.dump(dict(sorted(content.items())), fp, indent=4, separators=[",", " = "])
        data_to_manipulate = json.dumps(dict(sorted(content.items())), indent=4, separators=[",", " = "])
        data_to_manipulate = re.sub('\s\s"', '  ', data_to_manipulate)
        data_to_manipulate = re.sub('\n\s\s\s\s},\n', '\n    }\n', data_to_manipulate)
        terraformed_key_names = re.sub('"\s=\s', ' = ', data_to_manipulate)
        fp.write(terraformed_key_names)
    with open(file_path_name, 'a', newline='\n') as fp:
        fp.write("\n")
