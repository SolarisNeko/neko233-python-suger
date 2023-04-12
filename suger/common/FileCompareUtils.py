import os
import string
import time
import hashlib
from typing import List

from suger.common import StringUtils, FileUtils, JsonUtils
from suger.common.CsvUtils import CsvUtils

DEFAULT_OUTPUT_FILE_NAME = 'file_compare_map.csv'


class FileCompareUtils:

    @staticmethod
    def writeCompareInfo(result_output_file='compare_by_history_file.txt',
                         input_scan_directory: string = './',
                         your_output_directory: string = './',
                         your_output_file_name: string = DEFAULT_OUTPUT_FILE_NAME,
                         isNeedMd5: bool = True,
                         history_data_file_full_path: string = 'file_compare_map.csv',
                         ):
        same_changed_objs, only_in_list1_objs, only_in_list2_objs \
            = FileCompareUtils.compare(input_scan_directory
                                       , your_output_directory
                                       , your_output_file_name
                                       , isNeedMd5
                                       ,
                                       history_data_file_full_path)

        FileUtils.writeStringToFile(result_output_file, 'is delete')
        FileUtils.writeStringToFile(result_output_file, CsvUtils.serialize(only_in_list1_objs), isAppend=True)
        FileUtils.writeStringToFile(result_output_file, '\nhave change\n', isAppend=True)
        FileUtils.writeStringToFile(result_output_file, CsvUtils.serialize(same_changed_objs), isAppend=True)
        FileUtils.writeStringToFile(result_output_file, '\nis createde\n', isAppend=True)
        FileUtils.writeStringToFile(result_output_file, CsvUtils.serialize(only_in_list2_objs), isAppend=True)

    @staticmethod
    def compare(input_scan_directory: string = './',
                your_output_directory: string = './',
                your_output_file_name: string = DEFAULT_OUTPUT_FILE_NAME,
                isNeedMd5: bool = True,
                history_data_file_full_path: string = 'file_compare_map.csv',
                ):
        newDtoList, output_file_name = FileCompareUtils.getFileCompareInfo(input_scan_directory,
                                                                           isNeedMd5,
                                                                           your_output_directory,
                                                                           your_output_file_name)

        old_csv_str = FileUtils.readFileToString(history_data_file_full_path)
        oldDtoList = CsvUtils.deserialize(old_csv_str, FileCompareDto)

        same_changed_objs, only_in_list1_objs, only_in_list2_objs = FileCompareUtils.compare_dto_lists(
            oldDtoList, newDtoList, 'fullpath')
        return same_changed_objs, only_in_list1_objs, only_in_list2_objs

    @staticmethod
    def compare_dto_lists(list1: List[object], list2: List[object], field: str):
        # 相同的对象
        same_pk_but_change_objs = []
        # list1 独有的对象
        only_in_list1_objs = []
        # list2 独有的对象
        only_in_list2_objs = []
        # 将 list1 和 list2 的所有对象按照 field 的值进行排序
        sorted_list1 = sorted(list1, key=lambda obj: getattr(obj, field))
        sorted_list2 = sorted(list2, key=lambda obj: getattr(obj, field))
        # 对比两个列表
        i = j = 0
        while i < len(sorted_list1) and j < len(sorted_list2):
            obj1 = sorted_list1[i]
            obj2 = sorted_list2[j]
            if getattr(obj1, field) < getattr(obj2, field):
                only_in_list1_objs.append(obj1)
                i += 1
            elif getattr(obj1, field) > getattr(obj2, field):
                only_in_list2_objs.append(obj2)
                j += 1
            else:
                # 如果两个对象的 field 相同，但其余内容不同，则加入 same_objs 列表
                if obj1 != obj2:
                    # same_pk_but_change_objs.append((obj1, obj2))
                    # 只反回新对象
                    same_pk_but_change_objs.append((obj2))
                i += 1
                j += 1

        # 将 list1 剩余的对象加入 only_in_list1_objs 列表
        while i < len(sorted_list1):
            only_in_list1_objs.append(sorted_list1[i])
            i += 1

        # 将 list2 剩余的对象加入 only_in_list2_objs 列表
        while j < len(sorted_list2):
            only_in_list2_objs.append(sorted_list2[j])
            j += 1

        return same_pk_but_change_objs, only_in_list1_objs, only_in_list2_objs

    @staticmethod
    def writeFileCompareInfo(input_scan_directory: string,
                             your_output_directory: string = './',
                             your_output_file_name: string = DEFAULT_OUTPUT_FILE_NAME,
                             isNeedMd5: bool = True
                             ):
        dataList, output_file_name = FileCompareUtils.getFileCompareInfo(input_scan_directory, isNeedMd5,
                                                                         your_output_directory,
                                                                         your_output_file_name)

        # Create a new file to store the file map
        with open(output_file_name, 'w') as f:
            # output
            csvList = CsvUtils.serialize(dataList)
            f.write(f'{csvList} \n')

    @staticmethod
    def getFileCompareInfo(input_scan_directory, isNeedMd5, your_output_directory, your_output_file_name):
        if (StringUtils.isBlank(input_scan_directory)):
            raise Exception(f'your scan_directory is blank')
        if (StringUtils.isBlank(your_output_directory)):
            raise Exception(f'your output_directory is blank')
        if (StringUtils.isBlank(your_output_file_name)):
            raise Exception(f'your output_directory is blank')

        # handle
        scan_directory = os.path.normpath(input_scan_directory.strip())
        output_directory = os.path.normpath(your_output_directory.strip())
        output_file_name = os.path.normpath(your_output_file_name.strip())
        output_file_full_path = FileUtils.getFullPath(os.path.normpath(f'{output_directory}/{output_file_name}'))

        print(f'output file full path = {output_file_full_path}')
        # Create an empty dictionary to store file paths and update times
        file_map = {}
        fileList = FileUtils.scanDir(scan_directory)
        # Loop through each file in the directory
        for filename in fileList:
            # Get the full path of the file
            to_handle_full_path = os.path.join(scan_directory, filename)
            # Get the update time of the file and convert it to a readable format
            update_time = time.strftime(
                '%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(to_handle_full_path)))
            # Add the file path and update time to the dictionary
            file_map[to_handle_full_path] = update_time

        dataList = []
        # Loop through each file path and update time in the dictionary
        for to_handle_full_path, update_time in file_map.items():

            temp_path = os.path.normpath(to_handle_full_path)
            # 获取当前文件的绝对路径
            linux_full_path = os.path.abspath(temp_path)

            if FileUtils.isNotFileExists(linux_full_path):
                continue

            if output_file_full_path == linux_full_path:
                continue

            md5_hash = None
            if (isNeedMd5):
                # Open the file in read-only binary mode
                with open(linux_full_path, 'rb') as read_file:
                    # Read the contents of the file
                    contents = read_file.read()
                    # Calculate the MD5 hash of the contents
                    md5_hash = hashlib.md5(contents).hexdigest()

            # Write the file path and update time to the file
            dto = FileCompareDto(
                fullpath=linux_full_path,
                update_time=update_time,
                md5_hash=md5_hash,
            )

            dataList.append(dto)
        return dataList, output_file_name


class FileCompareDto:
    def __init__(self,
                 fullpath: string,
                 update_time: string,
                 md5_hash: string
                 ):
        self.fullpath = fullpath
        self.update_time = update_time
        self.md5_hash = md5_hash


if __name__ == '__main__':
    # FileCompareUtils.writeFileCompareInfo(input_scan_directory='./',
    #                                       isNeedMd5=True)
    FileCompareUtils.writeCompareInfo(input_scan_directory='./',
                                      isNeedMd5=True)