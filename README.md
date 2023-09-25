# Manjaro Snapshot OS
## An immutable Manjaro Linux utilizing btrfs snapshots  
A huge thank you to @lambdanil for the original project at [lambdanil/astOS](https://github.com/lambdanil/astOS) 

## Table of contents

---
* [What is Manjaro Snapshot OS?](https://github.com/fhdk/msos#what-is-Manjaro-Snapshot-OS)
* [Additional documentation](https://github.com/fhdk/msos#additional-documentation)
  * [Installation](https://github.com/fhdk/msos#installation)
  * [Post installation](https://github.com/fhdk/msos#post-installation-setup)
  * [Snapshot management and deployments](https://github.com/fhdk/msos#snapshot-management)
  * [Package management](https://github.com/fhdk/msos#package-management)
* [Additional documentation](https://github.com/fhdk/msos#additional-documentation)
  * [Updating the pacman keys](https://github.com/fhdk/msos#fixing-pacman-corrupt-packages--key-issues)
  * [Saving configuration changes in /etc persistently](https://github.com/fhdk/msos#saving-configuration-changes-made-in-etc)
  * [Updating mast itself](https://github.com/fhdk/msos#updating-mast-itself)
  * [Debugging ast](https://github.com/fhdk/msos#debugging-ast)
* [Known bugs](https://github.com/fhdk/msos#known-bugs)
* [Contributing](https://github.com/fhdk/msos#contributing)
* [Community](https://github.com/fhdk/msos#community)


## What is Manjaro Snapshot OS?

---
Manjaro Snapshot OS uses an immutable (read-only) root filesystem.  
Software is installed and configured into individual snapshot trees, which can then be deployed and booted into.
**This has several advantages:**

* Security
  * Even if running an application with eleveted permissions, it cannot replace system libraries with malicious versions
* Stability and reliability
  * Due to the system being mounted as read only, it's not possible to accidentally overwrite system files
  * If the system runs into issues, you can easily roll back the last working snapshot within minutes
  * Atomic updates - Updating your system all at once is more reliable
  * Thanks to the snapshot feature, astOS can ship cutting edge software without becoming unstable
  * Manjaro Snapshot needs maintenance like everything else, so it has a built-in automated update tool that creates snapshots before updates and automatically checks if the system upgraded properly before deploying the new snapshot
* Configurability
  * With the snapshots organised into a tree, you can have multiple different configurations of your software available, with varying packages, without any interference
  * For example: you can have a single desktop installed and then have 2 snapshots on top - one for gming, with the newest kernel and drivers, and the other for work, with the LTS kernel and more stable software, allowing you to switch between these depending on what you want to do
  * You can also easily try out software without having to worry about breaking your system or polluting it with unnecessary files, for example you can try out a new desktop environment in a snapshot and then delete the snapshot, without modifying your main system at all
  * This can also be used for multi-user systems, where each user has a completely separate system with different software, and yet they can share certain packages such as kernels and drivers
  * Manjaro Snapshot allows you to install software by chrooting into snapshots
  * Manjaro Snapshot is very customizable as you can choose exactly which software you want to use
* It also makes for a good workstation or general use distribution utilizing development containers and flatpak for desktop applications 

## Installation

---
Manjaro Snapshot can be installed using a special Manjaro Architect iso and an internet connection is mandatory to be able to install the system using Manjaro Snapshot OS.

Manjaro Snapshot has 4 installation profiles, one for minimal installation and three profiles for vanilla Gnome, Plasma and Xfce.

```
git clone "https://github.com/fhdk/msos"  
cd msos
```
Locate your device
```
lsblk
```
**IMPORTANT**
The installer will complete erase the device - so be sure you get it right
```
python main.py /dev/sdy
```

## Post installation setup
* Post installation setup is not necessary if you install one of the desktop editions (Gnome or KDE)
* A lot of information for how to handle post-install setup is available on the [ArchWiki page](https://wiki.archlinux.org/title/general_recommendations) 
* Here is a small example setup procedure:
  * Start by creating a new snapshot from `base` using `mast clone 0`
  * Chroot inside this new snapshot (`mast chroot <snapshot>`) and begin setup
    * Start by adding a new user account: `useradd username`
    * Set the user password `passwd username`
    * Now set a new password for root user `passwd root`
    * Now you can install additional packages (desktop environments, container technologies, flatpak) using pacman
    * Once done, exit the chroot with `exit 0`
    * Then you can deploy it with `mast deploy <snapshot>`

## Additional documentation
* It is advised to refer to the [Manjaro wiki](https://wiki.manjaro.org/) for documentation not part of this project
* Report issues/bugs on the [Github issues page](https://github.com/fhdk/msos/issues)
* **HINT: you can use `mast help` to get a quick overview of available commands**

### Base snapshot
* The snapshot `0` is reserved for the base system snapshot, it cannot be changed and can only be updated using `mast base-update`

## Snapshot Management
### Show filesystem tree
```
   mast tree
```
* The output can look for example like this:
```
   root - root
   ├── 0 - base snapshot
   └── 1 - multiuser system
       └── 4 - applications
           ├── 6 - MATE full desktop
           └── 2*- Plasma full desktop
```
* The asterisk shows which snapshot is currently selected as default
* You can also get only the number of the currently booted snapshot with
```
   mast current
```
### Add descritption to snapshot
#### Snapshots allow you to add a description to them for easier identification
```
mast desc <snapshot> <description>
```
### Delete a tree
#### Remove a snapshot tree
```
mast del <tree>
```
### Custom boot configuration
If you need to use a custom grub configuration, chroot into a snapshot and edit `/etc/default/grub`, then deploy the snapshot and reboot

### chroot into snapshot 
```
mast chroot <snapshot>
```
Once inside the chroot the OS behaves like regular Manjaro, so you can install and remove packages using pacman or pamac.
**Do not run mast from inside a chroot**, it could cause damage to the system, there is a failsafe in place, which can be bypassed with `--chroot` if you really need to (not recommended).  
The chroot has to be exited properly with `exit 0`, otherwise the changes made will not be saved.
To discard the changes made, use `exit 1` instead.
If you don't exit chroot the "clean" way with `exit 0`, it's recommended to run `mast tmp` to clear temporary files left behind

### unlocked shell inside active snapshot
You can enter an unlocked shell inside the current booted snapshot with
```
mast live-chroot
```
* The changes made to live session are not saved on new deployments 

### Other chroot options
Run a specified command inside snapshot
```
mast run <snapshot> <command>
```
Run a specified command inside snapshot and all it's branches
```
mast tree-run <tree> <command>
```

### Clone snapshot
```
mast clone <snapshot>
```

### Clone a tree
```
mast clone-tree <snapshot>
```

### Add branch to snapshot
```
mast branch <snapshot>
```

### Clone snapshot under same parent
```
mast cbranch <snapshot>
```

### Clone snapshot under specified parent
* Make sure to sync the tree after
```
mast ubranch <parent> <snapshot>
```

### Create new tree
```
mast new
```

### Deploy snapshot
```
mast deploy <snapshot>  
```
Reboot to use the new snapshot after deploying

### Update base snapshot
```
mast base-update
```
**Note**: the base itself is located at `/.snapshots/rootfs/snapshot-0` with `/etc` being located at `/.snapshots/etc/etc-0` respectively, therefore if you really need to make a configuration change, you can mount snapshot these as read-write and then snapshot back as read only.

## Package management

### Software installation
* Software can also be installed using pacman in a chroot
* AUR can be used under the chroot (requires configuration)
* Flatpak can be used for persistent package installation
* Using containers for additional software installation is also an option. 
  - One example [distrobox](https://github.com/89luca89/distrobox)
```
mast install <snapshot> <package>
```
* After install you can sync the newly installed packages to all the branches of the tree with
* Syncing the tree also updates all the snapshots
```
mast sync <tree>
```
* To sync without updating (may cause package duplication in database)
```
mast force-sync <tree>
```

#### Removing software
* For a single snapshot
```
   mast remove <snapshot> <package or packages>
```
* Recursively
```
   mast tree-rmpkg <tree> <pacakge or packages>
```

#### Updating
* It is advised to clone a snapshot before updating it, so you can roll back in case of failure
* This update only updates the system packages, in order to update mast itself see [this section](https://github.com/fhdk/msos#updating-mast-itself)
* To update a single snapshot
```
   mast upgrade <snapshot>
```
* To recursively update an entire tree
```
   mast tree-upgrade <tree>
```
* This can be configured in a script (ie. a crontab script) for easy and safe automatic updates
* If the system becomes unbootable after an update, you can boot last working deployment (select in grub menu) and then perform a rollback
```
   mast rollback
```
* Then you can reboot back to a working system

## Extras

#### Fixing pacman corrupt packages / key issues
* Arch's pacman package manager sometimes requires a refresh of the PGP keys
* To fix this issue we can simply reinstall they arch keyring
```
   mast install <snapshots> manjaro-keyring archlinux-keyring
```
#### Saving configuration changes made in `/etc`
* Normally configuration should be done with `mast chroot`, but sometimes you may want to apply changes you've made to the booted system persistently
* To do this use the following command
```
   mast etc-update
```
* This allows you to configure your system by modifying `/etc` as usual, and then saving these changes

#### Updating mast itself
* mast doesn't get updated alongside the system when `mast upgrade` is used
* sometimes it may be necessary to update mast itself
* mast can be updated with a single command
```
   mast mast-sync
```

#### Debugging ast
Sometimes it may be necessary to debug the script
- copy `mast` to any location:
```
   cp /usr/bin/mast mastpk.py
```
- run with `--debug` to show outputs

## Known bugs

* When running mast without arguments - IndexError: list index out of range
* Running mast without root permissions shows permission denied errors instead of an error message
* Swap partition doesn't work, it's recommended to use a swapfile or zram instead
* Docker has issues with permissions, to fix run
```
   sudo chmod 666 /var/run/docker.sock
```
* If you run into any issues, report them on [the issues page](https://github.com/fhdk/msos/issues)

# Contributing
* Code and documentation contributions are welcome
* Bug reports are a good way of contributing to the project too
* Before submitting a pull request test your code and make sure to comment it properly

# Community
* [Manjaro Forum](https://forum.manjaro.org)

---

**Project is licensed under the AGPLv3 license**

