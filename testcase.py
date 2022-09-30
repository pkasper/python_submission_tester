from CONFIG import *

import subprocess
import os
import shutil
import uuid
import zipfile
import tarfile
import string
import importlib.machinery


class Testcase:
    def __init__(self, _mat_nr, _submission, _testcase_dir):
        self.mat_nr = _mat_nr
        self.progress = None
        self._submission = _submission
        self._testcase_dir = _testcase_dir
        self._tests = self._load_testcase()
        self._temp_dir = None
        self._subfolder = ""

    def run(self):
        self._prepare_folder()

        results = dict()
        for test_id, test_config in self._tests.items():
            results[test_id] = self._execute_testcase(test_id, test_config)

        self._cleanup()
        return results

    def _load_testcase(self):
        try:
            import_mod_path = self._testcase_dir.replace(os.path.sep, ".") + TESTCASE_SCRIPTS_FILE[:-3]
            #__import__(import_mod_path, globals(), locals())
            globals().update(importlib.import_module(import_mod_path).__dict__)
        except Exception as _e:  # No scripts file
            pass
        testcase_file_path = self._testcase_dir + TESTCASE_FILE
        if not os.path.isfile(testcase_file_path):
            raise FileNotFoundError("Testcase file not found")

        with open(testcase_file_path, "r") as testcase_file:
            return eval(testcase_file.read())

    def _cleanup(self):
        shutil.rmtree(self._temp_dir, ignore_errors=True)
        return

    def _prepare_folder(self):
        self._temp_dir = TEMP_DIR + str(uuid.uuid4()) + "/"

        archive_path = os.path.dirname(self._submission)
        archive_file = os.path.basename(self._submission)
        archive_name, archive_ext = os.path.splitext(archive_file)

        os.makedirs(self._temp_dir)

        if archive_ext == ".zip":
            with zipfile.ZipFile(self._submission, "r") as archive:
                archive.extractall(self._temp_dir)
        elif archive_ext == ".gz":
            with tarfile.open(self._submission, "r") as archive:
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner) 
                    
                
                safe_extract(archive, self._temp_dir)

        dir_listing = os.listdir(self._temp_dir)
        if len(dir_listing) == 1 and os.path.isdir(dir_listing[0]):
            self._subfolder = dir_listing[0] + "/"

    def _execute_testcase(self, _id, _config):
        if "input" in _config:
            for input_link in _config['input']:
                os.symlink(os.getcwd() + "/" + self._testcase_dir + input_link['target'], self._temp_dir + self._subfolder + input_link['link'])

        if "output" in _config:
            for output_dir in _config['output']:
                if os.path.exists(self._temp_dir + self._subfolder + output_dir):
                    shutil.rmtree(self._temp_dir + self._subfolder + output_dir)
                os.makedirs(self._temp_dir + self._subfolder + output_dir)

        success = False

        call_package = ["python", _config['script_name']]
        if _config['params'] is not None:
            if isinstance(_config['params'], str):
                call_package.append(_config['params'])
            elif isinstance(_config['params'], list):
                call_package += _config['params']
        if _config['type'] == "exit":
            try:
                task_process = subprocess.Popen(call_package,
                                                cwd=self._temp_dir + self._subfolder,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
                std_out, std_err = task_process.communicate()
                exit_code = task_process.returncode
                # print(exit_code)
                if exit_code == 0:
                    success = True

            except Exception as error_text:
                print("EXCEPTION RAISED")
                print(error_text)
                return False
            finally:
                for input_link in _config['input']:
                    os.unlink(self._temp_dir + self._subfolder + input_link['link'])

        if _config['type'] == "exec":
            success = True
            validaion_success = True
            try:
                task_process = subprocess.Popen(call_package,
                                                cwd=self._temp_dir + self._subfolder,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
                std_out, std_err = task_process.communicate()
                console_output = std_out.decode().strip().replace("\r\n", "\n")

                if "validate" in _config:
                    #print("OUT", std_out)
                    #print("ERR", std_err)
                    for validation_function in _config['validate']:
                        if not validation_function(self._temp_dir):
                            validaion_success = False
                            break
            except Exception as error_text:
                print("EXCEPTION RAISED")
                print(error_text)
                return False
            finally:
                for input_link in _config['input']:
                    os.unlink(self._temp_dir + self._subfolder + input_link['link'])

            for diff_object in _config["console"]:
                success = False
                if diff_object['type'] == "exact":
                    for target_option in diff_object['target']:
                        if console_output == target_option:
                            success = True
                            break

                if diff_object['type'] == "contains":
                    for target_option in diff_object['target']:
                        if target_option in console_output:
                            success = True
                            break
                if not success:
                    break

            success = success & validaion_success
        print("[{mat_nr}] {test_id} {test_name}: {success}".format(mat_nr=self.mat_nr,
                                                                   test_id=_id,
                                                                   test_name=_config['name'],
                                                                   success="OK" if success else "FAILED"))

        return success
