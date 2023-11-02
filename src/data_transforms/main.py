import argparse
import logging
import os
import transforms

logger = logging.getLogger(__name__)

class DataTransform:

    def __init__(self):
        self.data_path = os.getcwd()
        self.input_directory = os.path.join(os.getcwd(), "generated")
        self.project_name = None

    @staticmethod
    def _parse_args():
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--data-path",
                    help="the local path for the Octopus server data, 'current' = the current work path")
        parser.add_argument("-id", "--input-directory", help="system path containing exported project data")
        parser.add_argument("-p", "--project-name", help="project name to process")

        args, unknown = parser.parse_known_args()
        return args

    def _process_args_to_configs(self):
        args = self._parse_args()

        if args.input_directory:
            self.input_directory = args.input_directory
        assert self.input_directory.endswith("/"), \
            f"input-directory must end with /; {self.input_directory} is invalid"

        if args.data_path:
            self.data_path = args.data_path
        assert self.input_directory.endswith("/"), \
            f"data-path must end with /; {self.data_path} is invalid"
        
        if args.project_name is not None:
            self.project_name = args.project_name
        else:
            raise ValueError("project-name must be specified")
        
        return args

    def run(self):
        args = self._process_args_to_configs()
        input_directory = os.path.join(self.input_directory, args.project_name)
        # output_directory = os.path.join(self.data_path, args.project_name)
        variable_lists = transforms.load_yaml_files(os.path.join(input_directory + "/Spaces-1/libraryvariablesets"), "Id")
        variables = transforms.load_yaml_files(os.path.join(input_directory + "/Spaces-1/variables"), "Id")
        merged_variables = transforms.merge_variable_sets(variables, variable_lists, args.project_name)

        # This was cool, but a decent amount of manual transformation still after processing.

        # normalized_parameters = transforms.normalize_parameters(merged_variables)
        # Get all this data out of here as HCL formatted locals blocks in tf files
        # for environ in {"staging", "production"}:
        #   for parameter_set in normalized_parameters:
        #     if normalized_parameters[parameter_set][environ]["parameters"] != {}:
        #         transforms.write_hcl_file(os.path.join(self.data_path + "/" + parameter_set + "/" + environ + "-parameters.tf"), normalized_parameters[parameter_set][environ]["parameters"], args.project_name, environ)
        #     if normalized_parameters[parameter_set][environ]["secrets"] != {}:
        #         transforms.write_hcl_file(os.path.join(self.data_path + "/" + parameter_set + "/" + environ + "-secrets.tf"), normalized_parameters[parameter_set][environ]["secrets"], args.project_name, environ)
        # transforms.export_project_variable_mappings(os.path.join(self.data_path + "setlists/" + args.project_name + "-parametersets.tf"), normalized_parameters, args.project_name)
        
        # Just make one massive local set for all the variables
        normalized_parameters_by_type = transforms.normalize_parameters_by_type(merged_variables)
        transforms.export_comprehensive_list(os.path.join(self.data_path + "fullset/" + args.project_name + ".tf"), normalized_parameters_by_type, args.project_name)
        transforms.export_project_variable_mappings(os.path.join(self.data_path + "fullset/" + args.project_name + "-parametersets.tf"), normalized_parameters_by_type, args.project_name)



def main():
    logger.info(f"********** Data Transforms - start **********")
    DataTransform().run()
    logger.info(f"********** Data Transforms - done **********")


if __name__ == "__main__":
    main()
