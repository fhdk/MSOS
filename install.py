#!/usr/bin/python3

# TODO: the installer needs a proper rewrite
# TODO: Use native functions instead of os.system()
# TODO: Append to package list instead of pacstrapping a gazillion times

import os
import shutil
import subprocess
import json
import sys
from subprocess import CalledProcessError, SubprocessError
from pkg_lists import packages, gnome, plasma

__version__ = "0.1-alpha"

BASE: int = 0
GNOME: int = 1
PLASMA: int = 2
BUILD_MIRROR = "https://manjaro.dk/repo"
INSTALL_HEADER: str = f"Manjaro Snapshot OS installer v{__version__}"
INSTALL_ROOT: str = "/mnt"
SNAPSHOTS_DIR: str = ".snapshots"
FS_PART_FILE: str = f"{SNAPSHOTS_DIR}/mast/part"
FS_TREE_FILE: str = f"{SNAPSHOTS_DIR}/mast/fstree"
MAST_PACMAN_DIR: str = "usr/share/mast/db"
MAST_SNAP_FILE: str = "usr/share/mast/snap"


class BColors:
    HEADER = '\033[95m'
    OK_BLUE = '\033[94m'
    OK_CYAN = '\033[96m'
    OK_GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END_C = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    NORMAL = "\033[1;37m"


def debug(where: str, what: str, value: str) -> None:
    print("{}[DEBUG]{}{} '{}={}'".format(BColors.WARNING, BColors.NORMAL, where, what, value))


def underline(message: str) -> None:
    print("{}{}{}".format(BColors.UNDERLINE, message, BColors.END_C))


def default(message: str) -> None:
    print("    {}{}{}".format(BColors.NORMAL, message, BColors.END_C))


def header(message: str) -> None:
    print("{}#### {}{}".format(BColors.HEADER, message, BColors.END_C))


def attention(message: str) -> None:
    print("{}  -> {}{}".format(BColors.OK_CYAN, message, BColors.END_C))


def ok_blue(message: str) -> None:
    print("{}[ OK ] {}{}".format(BColors.OK_BLUE, message, BColors.END_C))


def ok_cyan(message: str) -> None:
    print("{}[ OK ] {}{}".format(BColors.OK_CYAN, message, BColors.END_C))


def ok_green(message: str) -> None:
    print("{}[ OK ] {}{}".format(BColors.OK_GREEN, message, BColors.END_C))


def fail(message: str) -> None:
    print("{}[FAIL] {}{}".format(BColors.FAIL, message, BColors.END_C))


def warning(message: str) -> None:
    print("{}[WARN] {} {}".format(BColors.WARNING, message, BColors.END_C))


def disk_path_to_uuid(partition: str) -> str:
    if fs_path_exist(partition):
        result = str(subprocess.check_output(f"blkid -s UUID -o value {partition}", shell=True))
        return result[2:len(result)-3]
    return ""


def disk_uuid_to_path(uuid: str) -> str:
    result = str(subprocess.check_output(f"blkid -U {uuid}", shell=True))
    return result[2:len(result)-3]


def fs_path_exist(path: str, file: bool = False) -> bool:
    if not file:
        return os.path.exists(path)
    return os.path.isfile(path)


def fs_rmtree(path: str) -> None:
    if fs_path_exist(path):
        shutil.rmtree(path, ignore_errors=True)


def get_tmp_mount() -> str:
    result = str(subprocess.check_output("cat /proc/mounts | grep ' / btrfs'", shell=True))
    if "tmp0" in result:
        return "tmp0"
    return "tmp"


def swap_tmp(name: str) -> str:
    if name is "tmp":
        return "tmp0"
    return "tmp"


def fs_mkdir(path: str) -> None:
    if not fs_path_exist(path):
        os.mkdir(path)


def fs_sub_create(target: str, stdout: bool = False, stderr: bool = False) -> None:
    try:
        subprocess.run(["btrfs", "sub", "create", f"{target}"], stdout=stdout, stderr=stderr)
    except (CalledProcessError, SubprocessError) as ex:
        fail(ex)


def clear():
    os.system(f"clear")


def pacstrap(pkg_list):
    excode = int(os.system(f'basestrap {INSTALL_ROOT} --needed {" ".join(pkg_list)}'))
    if excode != 0:
        print("Failed to download packages!")
    return excode


def add_desktop_user() -> str:
    header("Create dsktop user")
    default("Enter username (all lowercase, max 8 letters)")
    username = input("# > ")
    while True:
        default("did your set username properly (y/n)?")
        reply = input("# > ")
        if reply.casefold() == "y":
            break
        else:
            clear()
            default("Enter username (all lowercase, max 8 letters)")
            username = input("# > ")

    os.system(f"arch-chroot {INSTALL_ROOT} useradd {username}")
    os.system(f"arch-chroot {INSTALL_ROOT} passwd {username}")
    while True:
        default("did your password set properly (y/n)?")
        reply = input("# > ")
        if reply.casefold() == "y":
            break
        else:
            clear()
            os.system(f"arch-chroot {INSTALL_ROOT} passwd {username}")

    return username


def configure_desktop(desktop: int, display_manager: str):
    pass


def main(args):
    device = f"{args[1]}"
    esp = f"{device}1"
    root = f"{device}2"
    username = ""
    # --------------------------------------------------------------------------------------------------
    # BEGIN ACCEPT
    header(INSTALL_HEADER)
    warning("The process wipes the selected block device")
    default(f"Target device is: '{device}'")
    default(f"The device will be partitioned and formatted")
    default(f"EFI partition on '{esp}' using FAT32 (1G)")
    default(f"root partition on '{root}' using btrfs")
    default(f"btrfs sub volume list ['@', '@.snapshots', '@home', '@var', '@etc', '@boot']")
    warning("Do you accept (y/n)")
    accept = ""
    while True:
        while accept.casefold() not in ['y', 'n', 'yes', 'no']:
            accept = input("# > ")
        if accept.casefold() in ['n', 'no']:
            ok_cyan("Terminated")
            sys.exit(1)
        break
    # END ACCEPT
    # --------------------------------------------------------------------------------------------------
    # BEGIN PREPARE SYSTEM
    header("Prepare system")
    attention("Setting buildmirror")
    os.system(f"pacman-mirrors -aU {BUILD_MIRROR}")
    ok_blue("Buildmirror set")
    attention("Updating host keyrings")
    os.system(f"pacman -Syy --noconfirm --needed archlinux-keyring manjaro-keyring")
    ok_blue("Updating keyrings")
    # END PREPARE SYSTEM
    # --------------------------------------------------------------------------------------------------
    # BEGIN PREPARE DISK
    attention("Prepare partitions")
    os.system(f"umount -R -f {INSTALL_ROOT}")
    os.system(f"umount -R -f {INSTALL_ROOT}")
    os.system(f"sgdisk --zap-all {device}")
    os.system(f"sgdisk --mbrtogpt {device}")
    os.system(f"sgdisk --new 1::+1G --typecode 1:ef00 --change-name 1:'EFI System' {device}")
    os.system(f"sgdisk --new 2::: --typecode 2:8300 --change-name 2:'Linux filesystem' {device}")
    ok_blue("Prepare partitions")
    attention("Formatting partitions")
    os.system(f"mkfs.vfat -F32 {esp}")
    os.system(f"mkfs.btrfs -f {root}")
    ok_blue("Partitions formatted")
    # END PREPARE DISK
    # --------------------------------------------------------------------------------------------------
    # BEGIN PROFILE SELECT
    header(INSTALL_HEADER)
    while True:
        header("Select install profile")
        default('''1. Minimal CLI system
    2. Desktop Gnome (vanilla)
    3. Desktop Plasma (vanilla)
    4. Desktop Xfce (vanilla)''')
        InstallProfile = str(input("# > "))
        if InstallProfile == "1":
            DesktopInstall = BASE
            break
        if InstallProfile == "2":
            DesktopInstall = GNOME
            break
        if InstallProfile == "3":
            DesktopInstall = PLASMA
            break
    # END PROFILE SELECT
    # --------------------------------------------------------------------------------------------------
    # BEGIN COLLECT BASE INFO
    header("Enter hostname")
    hostname = input("# > ")

    header("Select a timezone (type list to list):")
    attention("e.g. Europe/Copenhagen")
    while True:
        zone = input("# > ")
        if zone == "list":
            os.system(f"ls /usr/share/zoneinfo | less")
        else:
            check = str(subprocess.check_output(f"ls /usr/share/zoneinfo/{zone}", shell=True, stderr=True))
            if check[2:len(check) - 3].split("/")[-1] == zone.split("/")[-1]:
                timezone = str(f"/usr/share/zoneinfo/{zone}")
                break
            warning("Timezone invalid (type list to list):")

    header("Select a locale (type list to list)")
    attention("e.g. en_DK")
    while True:
        locale = input("# > ")
        if locale == "list":
            os.system(f"ls /usr/share/i18n/locales | less")
        else:
            check = str(subprocess.check_output(f"ls /usr/share/i18n/locales/{locale}", shell=True, stderr=True))
            if check[2:len(check) - 3].split("/")[-1] == locale:
                break
            warning("Locale invalid (type list to list)")

    header("Select keyboard layout (type list to list)")
    attention("e.g. dk-latin1")
    while True:
        keymap = input("# > ")
        if keymap == "list":
            os.system(f"localectl list-keymaps | less")
        else:
            check = str(subprocess.check_output(f"localectl list-keymaps", shell=True, stderr=True))
            if keymap in check[2:len(check) - 3].split("\\n"):
                break
            warning("layout invalid (type list to list)")
    # END COLLECT BASE INFO
    # --------------------------------------------------------------------------------------------------
    # BEGIN PREPARE BTRFS
    header("Prepare btrfs ...")
    os.system(f"mount {root} {INSTALL_ROOT}")
    btrdirs = ["@", f"@{SNAPSHOTS_DIR}", "@home", "@var", "@etc", "@boot", "@swapfile"]
    mntdirs = ["", f"{SNAPSHOTS_DIR}", "home", "var", "etc", "boot", "swapfile"]

    for btrdir in btrdirs:
        fs_sub_create(f"{INSTALL_ROOT}/{btrdir}")
    os.system(f"umount -R -f {INSTALL_ROOT}")
    for mntdir in mntdirs:
        os.system(f"mkdir -p {INSTALL_ROOT}/{mntdir}")
        if mntdir == "swapfile":
            swap = mntdir
            os.system(f"mount {root} -o subvol={btrdirs[mntdirs.index(swap)]},compress=none,noatime {INSTALL_ROOT}/{swap}")
            os.system(f"truncate -s 0 {INSTALL_ROOT}/{swap}")
            os.system(f"chattr +C {INSTALL_ROOT}/{swap}")
            os.system(f"dd if=/dev/zero of=/{swap} bs=1M count=4096 status=progress")
            os.system(f"chmod 600 /{swap}")
            os.system(f"mkswap /{swap}")
            os.system(f"swapon /{swap}")
            continue
        os.system(f"mount {root} -o subvol={btrdirs[mntdirs.index(mntdir)]},compress=zstd,noatime {INSTALL_ROOT}/{mntdir}")
    for i in ("tmp", "root"):
        os.system(f"mkdir -p {INSTALL_ROOT}/{i}")
    for i in ("ast", "boot", "etc", "root", "rootfs", "tmp", "var"):
        os.system(f"mkdir -p {INSTALL_ROOT}/{SNAPSHOTS_DIR}/{i}")
    for i in ("root", "tmp"):
        os.system(f"mkdir -p {INSTALL_ROOT}/{SNAPSHOTS_DIR}/mast/{i}")
    # END PREPARE BTRFS
    # --------------------------------------------------------------------------------------------------
    # BEGIN PREPARE EFI
    efi = os.path.exists("/sys/firmware/efi")
    if efi:
        os.system(f"mkdir {INSTALL_ROOT}/boot/efi")
        os.system(f"mount {esp} {INSTALL_ROOT}/boot/efi")
        packages.append("efibootmgr")
    # END PREPARE EFI
    # --------------------------------------------------------------------------------------------------
    # INSTALL PROFILE
    if DesktopInstall == GNOME:
        packages.extend(gnome)
    if DesktopInstall == PLASMA:
        packages.extend(plasma)
    while True:
        if pacstrap(packages):
            retry = ""
            warning("Error occured. Retry? (y/n)")
            while retry.casefold() not in ['y', 'n', 'yes', 'no']:
                retry = input("# > ")
                warning("Error occured. Retry? (y/n)")
            if retry.casefold() in ['n', 'no']:
                # makes no sense to continue
                fail("Error during package sync. Terminated.")
                sys.exit(1)
        else:
            break
    # END PACKAGE LIST INSTALLATION
    # --------------------------------------------------------------------------------------------------
    # BEGIN WRITE SYSTEM CONFIGURATION
    root_uuid = disk_path_to_uuid(root)
    esp_uuid = disk_path_to_uuid(esp)

    attention("configure fstab")
    with open(f'{INSTALL_ROOT}/etc/fstab', 'a') as f:
        f.write(f'UUID={root_uuid} / btrfs subvol=@,compress=zstd,noatime,ro 0 0\n')
        for mntdir in mntdirs[1:]:
            if mntdir == "swapfile":
                f.write(f'/swapfile none swap defaults 0 0\n')
                continue
            f.write(f'UUID={root_uuid} /{mntdir} btrfs subvol=@{mntdir},compress=zstd,noatime 0 0\n')
        if efi:
            f.write(f'UUID={esp_uuid} /boot/efi vfat umask=0077 0 2\n')
        f.write(f'/{SNAPSHOTS_DIR}/mast/root /root none bind 0 0\n')
        f.write(f'/{SNAPSHOTS_DIR}/mast/tmp /tmp none bind 0 0\n')

    os.system(f"mkdir -p {INSTALL_ROOT}/{MAST_PACMAN_DIR}")
    os.system(f"echo '0' > {INSTALL_ROOT}/{MAST_SNAP_FILE}")

    attention("configure pacman")
    os.system(f"cp -r {INSTALL_ROOT}/var/lib/pacman/* {INSTALL_ROOT}/{MAST_PACMAN_DIR}")
    os.system(f'sed -i s,"#DBPath      = /var/lib/pacman/","DBPath      = {MAST_PACMAN_DIR}/",g {INSTALL_ROOT}/etc/pacman.conf')
    os.system(f'sed -i s,"#Color","Color",g {INSTALL_ROOT}/etc/pacman.conf')
    os.system(f'sed -i s,"^#ParallelDownloads = 5","ParallelDownloads = 5",g {INSTALL_ROOT}/etc/pacman.conf')
    os.system(f'sed -i "/^ParallelDownloads/i ILoveCandy" {INSTALL_ROOT}/etc/pacman.conf')
    # ---- inject nix repo ----
    os.system(f"echo '\n\n[nixrepo]' >> {INSTALL_ROOT}/etc/pacman.conf")
    os.system(f"echo 'SigLevel = Optional TrusAll' >> {INSTALL_ROOT}/etc/pacman.conf")
    os.system(f"echo 'Server = https://uex.dk/nixrepo' >> {INSTALL_ROOT}/etc/pacman.conf")

    attention("configure clock")
    os.system(f"arch-chroot {INSTALL_ROOT} hwclock --utc --systohc")

    attention("configure timezone")
    os.system(f"arch-chroot {INSTALL_ROOT} ln -sf {timezone} /etc/localtime")

    attention("configure locale")
    os.system(f"echo 'en_US.UTF-8 UTF-8' >> {INSTALL_ROOT}/etc/locale.gen")
    os.system(f"echo '{locale}.UTF-8 UTF-8' >> {INSTALL_ROOT}/etc/locale.gen")
    os.system(f"arch-chroot {INSTALL_ROOT} locale-gen")
    os.system(f"echo 'LANG={locale}.UTF-8' > {INSTALL_ROOT}/etc/locale.conf")
    os.system(f"echo 'KEYMAP={keymap}' > {INSTALL_ROOT}/etc/vconsole.conf")
    os.system(f"echo 'FONT=' > {INSTALL_ROOT}/etc/vconsole.conf")
    os.system(f"echo 'FONT_MAP=' > {INSTALL_ROOT}/etc/vconsole.conf")

    attention("configure hostname")
    os.system(f"echo {hostname} > {INSTALL_ROOT}/etc/hostname")

    attention("configure hosts")
    os.system(f"echo '127.0.0.1 locahost' > {INSTALL_ROOT}/etc/hosts")
    os.system(f"echo '::1 locahost ip6-localhost ip6-loopback' >> {INSTALL_ROOT}/etc/hosts")
    os.system(f"echo 'ff02::1 ip6-allnodes' >> {INSTALL_ROOT}/etc/hosts")
    os.system(f"echo 'ff02::2 ip6-allrouters' >> {INSTALL_ROOT}/etc/hosts")
    os.system(f"echo '# This host address' >> {INSTALL_ROOT}/etc/hosts")
    os.system(f"echo '127.0.1.1 {hostname}' >> {INSTALL_ROOT}/etc/hosts")

    attention("configure fstab snapshots")
    sedex = ("0,/@/{s,@,@" + SNAPSHOTS_DIR + "/rootfs/snapshot-tmp,}",
             "0,/@etc/{s,@etc,@" + SNAPSHOTS_DIR + "/etc/etc-tmp,}",
             "0,/@boot/{s,@boot,@" + SNAPSHOTS_DIR + "/boot/boot-tmp,}",
             # "0,/ @ var/ {s, @ var, @"+SNAPSHOTS_DIR+"/var/var-tmp,}"
             )
    for sed in sedex:
        os.system(f"sed -i '{sed}' {INSTALL_ROOT}/etc/fstab")

    os.system(f"mkdir -p {INSTALL_ROOT}/{SNAPSHOTS_DIR}/mast/snapshots")
    os.system(f"cp ./mastpk.py {INSTALL_ROOT}/{SNAPSHOTS_DIR}/mast/mast")
    os.system(f"arch-chroot {INSTALL_ROOT} chmod +x /{SNAPSHOTS_DIR}/mast/mast")
    os.system(f"arch-chroot {INSTALL_ROOT} ln -s /{SNAPSHOTS_DIR}/mast /var/lib/mast")
    os.system(f"arch-chroot {INSTALL_ROOT} chmod 700 /{SNAPSHOTS_DIR}/mast/root")
    os.system(f"arch-chroot {INSTALL_ROOT} chmod 1777 /{SNAPSHOTS_DIR}/mast/tmp")

    if DesktopInstall is BASE:
        header("create root password")
        # Don't ask for password if doing a desktop install,
        # since root account will be locked anyway (sudo used instead)
        os.system(f"arch-chroot {INSTALL_ROOT} passwd")
        while True:
            print("did your password set properly (y/n)?")
            reply = input("> ")
            if reply.casefold() == "y":
                break
            else:
                clear()
                os.system(f"arch-chroot {INSTALL_ROOT} passwd")

    os.system(f"arch-chroot {INSTALL_ROOT} systemctl enable NetworkManager")
    fstree = {"name": "root", "children": [{"name": "0"}]}
    if DesktopInstall:
        fstree = {"name": "root", "children": [{"name": "0"}, {"name": "1"}]}
        os.system(f"echo '{root_uuid}' > {INSTALL_ROOT}/{FS_PART_FILE}")
    # write fstree to file
    with open(f"{INSTALL_ROOT}/{FS_TREE_FILE}", "w") as outfile:
        json.dump(fstree, outfile)
    # END WRITE SYSTEM CONFIGURATION
    # --------------------------------------------------------------------------------------------------
    # BEGIN BOOT CONFIGURATION
    attention("configure bootloader")
    os.system(f"arch-chroot {INSTALL_ROOT} sed -i 's/Manjaro/Manjaro Snapshot/g' /etc/default/grub")
    os.system(f"arch-chroot {INSTALL_ROOT} sed -i 's/GRUB_SAVEDEFAULT=true/GRUB_SAVEDEFAULT=false/g' /etc/default/grub")
    os.system(f"arch-chroot {INSTALL_ROOT} grub-install {device}")
    os.system(f"arch-chroot {INSTALL_ROOT} grub-mkconfig {device} -o /boot/grub/grub.cfg")
    grub_sed = "0,/subvol=@/{s,subvol=@,subvol=@" + SNAPSHOTS_DIR + "/rootfs/snapshot-tmp,g}"
    os.system(f"sed -i '{grub_sed}' {INSTALL_ROOT}/boot/grub/grub.cfg")
    os.system(f"arch-chroot {INSTALL_ROOT} ln -s /{SNAPSHOTS_DIR}/mast/mast /usr/local/bin/mast")
    os.system(f"btrfs sub snap -r {INSTALL_ROOT} {INSTALL_ROOT}/{SNAPSHOTS_DIR}/rootfs/snapshot-0")
    os.system(f"btrfs sub create {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-tmp")
    # os.system(f"btrfs sub create {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp")
    os.system(f"btrfs sub create {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-tmp")
    # os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/var/* {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp")
    # for i in ("pacman", "systemd"):
    #     os.system(f"mkdir -p {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp/lib/{i}")
    # os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/var/lib/pacman/* {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp/lib/pacman/")
    # os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/var/lib/systemd/* {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp/lib/systemd/")
    os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/boot/* {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-tmp")
    os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/etc/* {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-tmp")
    #    os.system(f"btrfs sub snap -r {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-0")
    os.system(f"btrfs sub snap -r {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-tmp {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-0")
    os.system(f"btrfs sub snap -r {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-tmp {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-0")
    os.system(f"echo '{root}' > {INSTALL_ROOT}/{FS_PART_FILE}")
    # END BOOT CONFIGURATION
    # --------------------------------------------------------------------------------------------------
    # BEGIN PROFILE CONFIG
    if DesktopInstall == 1:
        os.system(f"echo '1' > {INSTALL_ROOT}/usr/share/mast/snap")

        username = add_desktop_user()

        os.system(f"arch-chroot {INSTALL_ROOT} usermod -aG audio,input,video,wheel {username}")
        os.system(f"arch-chroot {INSTALL_ROOT} passwd -l root")
        os.system(f"chmod +w {INSTALL_ROOT}/etc/sudoers")
        os.system(f"echo '%wheel ALL=(ALL:ALL) ALL' >> {INSTALL_ROOT}/etc/sudoers")
        os.system(f"chmod -w {INSTALL_ROOT}/etc/sudoers")
        os.system(f"arch-chroot {INSTALL_ROOT} mkdir /home/{username}")
        os.system(f"echo 'export XDG_RUNTIME_DIR=\"/run/user/1000\"' >> /home/{username}/.bashrc")
        os.system(f"arch-chroot {INSTALL_ROOT} chown -R {username} /home/{username}")
        os.system(f"arch-chroot {INSTALL_ROOT} systemctl enable gdm")
        os.system(f"arch-chroot {INSTALL_ROOT} systemctl enable systemd-timesyncd")

        os.system(f"cp -r {INSTALL_ROOT}/var/lib/pacman/* {INSTALL_ROOT}/usr/share/mast/db")

        os.system(f"btrfs sub snap -r {INSTALL_ROOT} {INSTALL_ROOT}/{SNAPSHOTS_DIR}/rootfs/snapshot-1")
        os.system(f"btrfs sub del {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-tmp")
        # os.system(f"btrfs sub del {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp")
        os.system(f"btrfs sub del {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-tmp")
        os.system(f"btrfs sub create {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-tmp")
        # os.system(f"btrfs sub create {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp")
        os.system(f"btrfs sub create {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-tmp")
        # os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/var/* {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp")
        # for i in ("pacman", "systemd"):
        #     os.system(f"mkdir -p {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp/lib/{i}")
        # os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/var/lib/pacman/* {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp/lib/pacman/")
        # os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/var/lib/systemd/* {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp/lib/systemd/")
        os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/boot/* {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-tmp")
        os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/etc/* {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-tmp")
        # os.system(f"btrfs sub snap -r {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-1")
        os.system(f"btrfs sub snap -r {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-tmp {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-1")
        os.system(f"btrfs sub snap -r {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-tmp {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-1")
        os.system(f"btrfs sub snap {INSTALL_ROOT}/{SNAPSHOTS_DIR}/rootfs/snapshot-1 {INSTALL_ROOT}/{SNAPSHOTS_DIR}/rootfs/snapshot-tmp")
        os.system(f"arch-chroot {INSTALL_ROOT} btrfs sub set-default /{SNAPSHOTS_DIR}/rootfs/snapshot-tmp")

    elif DesktopInstall == 2:
        os.system(f"echo '1' > {INSTALL_ROOT}/usr/share/mast/snap")

        username = add_desktop_user()

        os.system(f"arch-chroot {INSTALL_ROOT} usermod -aG audio,input,video,wheel {username}")
        os.system(f"arch-chroot {INSTALL_ROOT} passwd -l root")
        os.system(f"chmod +w {INSTALL_ROOT}/etc/sudoers")
        os.system(f"echo '%wheel ALL=(ALL:ALL) ALL' >> {INSTALL_ROOT}/etc/sudoers")
        os.system(f"echo '[Theme]' > {INSTALL_ROOT}/etc/sddm.conf")
        os.system(f"echo 'Current=breeze' >> {INSTALL_ROOT}/etc/sddm.conf")
        os.system(f"chmod -w {INSTALL_ROOT}/etc/sudoers")
        os.system(f"arch-chroot {INSTALL_ROOT} mkdir /home/{username}")
        os.system(f"echo 'export XDG_RUNTIME_DIR=\"/run/user/1000\"' >> /home/{username}/.bashrc")
        os.system(f"arch-chroot {INSTALL_ROOT} chown -R {username} /home/{username}")
        os.system(f"arch-chroot {INSTALL_ROOT} systemctl enable sddm")
        os.system(f"arch-chroot {INSTALL_ROOT} systemctl enable systemd-timesyncd")

        os.system(f"cp -r {INSTALL_ROOT}/var/lib/pacman/* {INSTALL_ROOT}/usr/share/mast/db")

        os.system(f"btrfs sub snap -r {INSTALL_ROOT} {INSTALL_ROOT}/{SNAPSHOTS_DIR}/rootfs/snapshot-1")
        os.system(f"btrfs sub del {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-tmp")
        # os.system(f"btrfs sub del {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp")
        os.system(f"btrfs sub del {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-tmp")
        os.system(f"btrfs sub create {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-tmp")
        # os.system(f"btrfs sub create {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp")
        os.system(f"btrfs sub create {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-tmp")
        # os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/var/* {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp")
        # for i in ("pacman", "systemd"):
        #     os.system(f"mkdir -p {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp/lib/{i}")
        # os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/var/lib/pacman/* {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp/lib/pacman/")
        # os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/var/lib/systemd/* {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp/lib/systemd/")
        os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/boot/* {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-tmp")
        os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/etc/* {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-tmp")
        # os.system(f"btrfs sub snap -r {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-1")
        os.system(f"btrfs sub snap -r {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-tmp {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-1")
        os.system(f"btrfs sub snap -r {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-tmp {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-1")
        os.system(f"btrfs sub snap {INSTALL_ROOT}/{SNAPSHOTS_DIR}/rootfs/snapshot-1 {INSTALL_ROOT}/{SNAPSHOTS_DIR}/rootfs/snapshot-tmp")
        os.system(f"arch-chroot {INSTALL_ROOT} btrfs sub set-default /{SNAPSHOTS_DIR}/rootfs/snapshot-tmp")

    else:
        os.system(f"btrfs sub snap {INSTALL_ROOT}/{SNAPSHOTS_DIR}/rootfs/snapshot-0 {INSTALL_ROOT}/{SNAPSHOTS_DIR}/rootfs/snapshot-tmp")
        os.system(f"arch-chroot {INSTALL_ROOT} btrfs sub set-default /{SNAPSHOTS_DIR}/rootfs/snapshot-tmp")
    # END PROFILE CONFIGURATION
    # --------------------------------------------------------------------------------------------------
    # BEGIN CLEANUP
    os.system(f"cp -r {INSTALL_ROOT}/root/. {INSTALL_ROOT}/{SNAPSHOTS_DIR}/root/")
    os.system(f"cp -r {INSTALL_ROOT}/tmp/. {INSTALL_ROOT}/{SNAPSHOTS_DIR}/tmp/")
    os.system(f"rm -rf {INSTALL_ROOT}/root/*")
    os.system(f"rm -rf {INSTALL_ROOT}/tmp/*")
    # os.system(f"umount {INSTALL_ROOT}/var")

    if efi:
        os.system(f"umount {INSTALL_ROOT}/boot/efi")

    os.system(f"umount {INSTALL_ROOT}/boot")
    # os.system(f"mkdir {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp")
    # os.system(f"mkdir {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/boot/boot-tmp")
    # os.system(f"mount {args[1]} -o subvol=@var,compress=zstd,noatime {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp")
    os.system(f"mount {root} -o subvol=@boot,compress=zstd,noatime {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-tmp")
    # os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-tmp/* {INSTALL_ROOT}/var")
    os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-tmp/* {INSTALL_ROOT}/boot")
    os.system(f"umount {INSTALL_ROOT}/etc")
    # os.system(f"mkdir {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/etc/etc-tmp")
    os.system(f"mount {root} -o subvol=@etc,compress=zstd,noatime {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-tmp")
    os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-tmp/* {INSTALL_ROOT}/etc")

    if DesktopInstall:
        os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-1/* {INSTALL_ROOT}/{SNAPSHOTS_DIR}/rootfs/snapshot-tmp/etc")
        # os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-1/* {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/rootfs/snapshot-tmp/var")
        os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-1/* {INSTALL_ROOT}/{SNAPSHOTS_DIR}/rootfs/snapshot-tmp/boot")
    else:
        os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/{SNAPSHOTS_DIR}/etc/etc-0/* {INSTALL_ROOT}/{SNAPSHOTS_DIR}/rootfs/snapshot-tmp/etc")
        # os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/var/var-0/* {INSTALL_ROOT}/{MAST_SNAPSHOTS_DIR}/rootfs/snapshot-tmp/var")
        os.system(f"cp --reflink=auto -r {INSTALL_ROOT}/{SNAPSHOTS_DIR}/boot/boot-0/* {INSTALL_ROOT}/{SNAPSHOTS_DIR}/rootfs/snapshot-tmp/boot")

    os.system(f"umount -R {INSTALL_ROOT}")
    os.system(f"mount {root} -o subvolid=0 {INSTALL_ROOT}")
    os.system(f"btrfs sub del {INSTALL_ROOT}/@")
    os.system(f"umount -R {INSTALL_ROOT}")
    # END CLEANUP
    # --------------------------------------------------------------------------------------------------
    # ALL COMPLETE
    header(INSTALL_HEADER)
    header("Installation complete")
    if username and DesktopInstall is not BASE:
        attention("The default root account is locked")
        attention(f"Your username is '{username}'")
        attention("For administrative tasks use 'sudo' to elevate privileges.")
        attention("Run 'mast help' for info about snapshot commands.")
    ok_blue("You may reboot your system now :)")


if __name__ == "__main__":

    try:
        if os.getuid() != 0:
            warning("Installer must be run as root - terminated")
            sys.exit(1)

        if not fs_path_exist("/sys/firmware/efi"):
            # no support for bios boot
            warning("EFI boot is the only supported mode for this installer - terminated")
            sys.exit(1)

        arguments = list(sys.argv)

        if len(arguments) != 2:
            fail("Argument error - no block device supplied")
            warning("Specify target device path e.g. '/dev/sda'")
            default("Available block devices:")
            os.system(f"lsblk")
            exit(1)

        main(arguments)

    except KeyboardInterrupt:
        print(f'\n{ok_blue("Interrupted by the user.")}')
        exit(1)

