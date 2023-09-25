#  Copyright (c) 2023.
#  Original project: https://github.com/lambdanil/astOS
#  License: GNU GPL, version 3 or later; https://www.gnu.org/licenses/gpl.html
#  Fork: https://github.com/fhdk/astOS
#  Modified by @linux-aarhus at ${DATE}

import os
import shutil
import subprocess
from subprocess import SubprocessError, CalledProcessError
from .msg import fail


def disk_path_to_uuid(partition: str) -> str:
    """
    Return UUID from given partition as a string - empty if not found
    :param partition:
    :return: str
    """
    if fs_path_exist(partition):
        result = str(subprocess.check_output(f"blkid -s UUID -o value {partition}", shell=True))
        return result[2:36]
    return ""


def disk_uuid_to_path(uuid: str) -> str:
    """
    Get device path from specified uuid
    :param uuid:
    :return: str
    """
    result = str(subprocess.check_output(f"blkid -U {uuid}", shell=True))
    return result[2:len(result)-3]


def fs_cpr_reflink(source: str, destination: str, stdout: bool = False, stderr: bool = False):
    """
    Recursively copy source to destination using reflink=auto
    :param source:
    :param destination:
    :param stdout:
    :param stderr:
    :return:
    """
    try:
        subprocess.run(["cp", "--reflink=auto", "-r", f"{source}", f"{destination}"], stdout=stdout, stderr=stderr)
    except (CalledProcessError, SubprocessError) as ex:
        print(ex)


def fs_mkdir(path: str) -> None:
    """
    Create the specified path
    :param path:
    :return:
    """
    if not fs_path_exist(path):
        os.mkdir(path)


def fs_path_exist(path: str, file: bool = False) -> bool:
    """
    Check if given file path exist, optionally return if path is a file
    :param path:
    :param file:
    :return: bool
    """
    if not file:
        return os.path.exists(path)
    return os.path.isfile(path)


def fs_rmtree(path: str) -> None:
    """
    Remove the specified path from filesystem
    :param path:
    :return:
    """
    if fs_path_exist(path):
        shutil.rmtree(path, ignore_errors=True)


def fs_sub_create(target: str, stdout: bool = False, stderr: bool = False) -> None:
    """
    Create btrfs sub volume
    :param target:
    :param stdout:
    :param stderr:
    :return:
    """
    try:
        subprocess.run(["btrfs", "sub", "create", f"{target}"], stdout=stdout, stderr=stderr)
    except (CalledProcessError, SubprocessError) as ex:
        fail(ex)


def fs_sub_default(target: str, stdout: bool = False, stderr: bool = False) -> None:
    """
    Set default btrfs sub volume
    :param target:
    :param stdout:
    :param stderr:
    :return:
    """
    try:
        subprocess.run(["btrfs", "sub", "set-default", f"{target}"], stdout=stdout, stderr=stderr)
    except (CalledProcessError, SubprocessError) as ex:
        fail(ex)


def fs_sub_delete(target: str, stdout: bool = False, stderr: bool = False) -> None:
    """
    Delete btrfs sub volume
    :param target:
    :param stdout:
    :param stderr:
    :return:
    """
    try:
        subprocess.run(["btrfs", "sub", "del", f"{target}"], stdout=stdout, stderr=stderr)
    except (CalledProcessError, SubprocessError) as ex:
        fail(ex)


def fs_sub_snap(source: str, destination: str, stdout: bool = False, stderr: bool = False) -> None:
    """
    Snap btrfs sub volume from source to destination
    :param source:
    :param destination:
    :param stdout:
    :param stderr:
    :return:
    """
    try:
        subprocess.run(["btrfs", "sub", "snap", f"{source}", f"{destination}"], stdout=stdout, stderr=stderr)
    except (CalledProcessError, SubprocessError) as ex:
        fail(ex)


def fs_sub_snap_r(source: str, destination: str, stdout: bool = False, stderr: bool = False) -> None:
    """
    Snap btrfs sub volume from source to destination
    :param source:
    :param destination:
    :param stdout:
    :param stderr:
    :return:
    """
    try:
        subprocess.run(["btrfs", "sub", "snap", "-r", f"{source}", f"{destination}"], stdout=stdout, stderr=stderr)
    except (CalledProcessError, SubprocessError) as ex:
        fail(ex)


def get_tmp_mount() -> str:
    """
    Get btrfs tmp mount
    :return:
    """
    result = str(subprocess.check_output("cat /proc/mounts | grep ' / btrfs'", shell=True))
    if "tmp0" in result:
        return "tmp0"
    return "tmp"
