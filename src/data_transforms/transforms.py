#!/usr/bin/env python3

import os
import yaml
import logging
import json
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

def merge_variable_sets(variables, variable_sets):
    for var in variables:
        if str(variables[var]['OwnerId']).startswith("Projects-"):
            variables[var].update({"Name": "Project Specific Variables"})
        else:
            foundSet = variable_sets[variables[var]['OwnerId']]
            variables[var].update({"Name": foundSet['Name']})
    return variables

def normalize_parameters(input):
    map = {"staging":{"secrets":{}, "parameters":{}}, "production":{"secrets":{}, "parameters":{}}}
    # We can assume that all variables are going to be overwritten by the Project Specific Variables, 
    # so let's sort our input set to process the Project Specific Variables last
    sortedkeys = sorted(input.keys())
    for set in sortedkeys:
        varset=input[set]["Variables"]
        for var in varset:
            if var["IsSensitive"]:
                varType = "secrets"
            else:
                varType = "parameters"

            if var["Scope"] == {}:
                map["staging"][varType].update({var["Name"]:var["Value"]})
                map["production"][varType].update({var["Name"]:var["Value"]})
            elif var["Scope"]["Environment"][0] == "Environments-1":
                map["staging"][varType].update({var["Name"]:var["Value"]})
            elif var["Scope"]["Environment"][0] == "Environments-2":
                map["production"][varType].update({var["Name"]:var["Value"]})
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