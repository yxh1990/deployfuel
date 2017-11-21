# WHAT TO DO (install fresh system rather than upgrade)
install

# INSTALLATION SOURCE (centos repository)
url --url=http://10.20.0.2:8080/centos/x86_64/

# REPOSITORIES FROM Nailgun
repo --name=2014.2-6.0 --baseurl=http://10.20.0.2:8080/2014.2-6.0/centos/x86_64

# KEYBOARD AND LANGUAGE CUSTOMIZATION
lang en_US.UTF-8
keyboard us

# WHICH TIMEZONE TO USE ON INSTALLED SYSTEM
timezone --utc Etc/UTC

# REBOOT AFTER INSTALLATION
reboot

firewall --disable
zerombr

# SET ROOT PASSWORD DEFAULT IS r00tme
rootpw --iscrypted $6$tCD3X7ji$1urw6qEMDkVxOkD33b4TpQAjRiCeDZx0jmgMhDYhfB9KuGfqO9OcMaKyUxnGGWslEDQ4HxTw7vcAMP85NxQe61

# AUTHENTICATION CUSTOMIZATION
authconfig --enableshadow --passalgo=sha512

# DISABLE SELINUX ON INSTALLED SYSTEM
selinux --disabled

# INSTALL IN TEXT MODE
text

# SKIP CONFIGURING X
skipx

# Suppress "unsupported hardware" warning
unsupported_hardware

# SSH user and some unknown random password,
# we're going to use SSH keys anyway
sshpw --username root --iscrypted $6$tCD3X7ji$1urw6qEMDkVxOkD33k2jjklHSDG2hg2234kJHESJ3hwhsjHshSJshHSJSh333je34DHJHDr4je4AMP85NxQe61

%include /tmp/partition.ks

# COBBLER EMBEDDED SNIPPET: 'network_config'
# CONFIGURES NETWORK INTERFACES DEPENDING ON
# COBBLER SYSTEM PARAMETERS
# Using "new" style networking config, by matching networking information to the physical interface's 
# MAC-address
%include /tmp/pre_install_network_config


# PREINSTALL SECTION
# HERE ARE COMMANDS THAT WILL BE LAUNCHED BEFORE
# INSTALLATION PROCESS ITSELF
%pre

# COBBLER EMBEDDED SNIPPET: 'log_ks_pre'
# CONFIGURES %pre LOGGING
set -x -v
exec 1>/tmp/ks-pre.log 2>&1

# Once root's homedir is there, copy over the log.
while : ; do
    sleep 10
    if [ -d /mnt/sysimage/root ]; then
        cp /tmp/ks-pre.log /mnt/sysimage/root/
        logger "Copied %pre section log to system"
        break
    fi
done &


# DOWNLOADS send2syslog.py AND LAUNCHES IT
# IN ORDER TO MONITOR LOG FILES AND SEND
# LINES FROM THOSE FILES TO SYSLOG
wget -O /tmp/send2syslog.py "http://10.20.0.2/cobbler/aux/send2syslog.py"
echo '{"hostname": "node3.domain.tld",
    "watchlist": [
        {"servers": [ {"host": "10.20.0.2"} ],
            "watchfiles": [
                {"tag": "install/anaconda", "log_type": "anaconda",
                    "files": ["/tmp/anaconda.log",
                        "/mnt/sysimage/root/install.log"]},
                {"tag": "install/ks-pre", "files": ["/tmp/ks-pre.log"]},
                {"tag": "install/ks-post", "files": ["/mnt/sysimage/root/ks-post.log"]},
                {"tag": "install/syslog", "log_type": "anaconda",
                    "files": ["/tmp/syslog"]},
                {"tag": "install/storage", "log_type": "anaconda",
                    "files": ["/tmp/storage.log"]}
            ]
        }
    ]
}' > /tmp/send2syslog.conf
python /tmp/send2syslog.py -c /tmp/send2syslog.conf


# SNIPPET: 'kickstart_ntp'
# SYNC LOCAL TIME VIA NTP
ntpdate -t 4 -b 10.20.0.2
hwclock --systohc


# COBBLER EMBEDDED SNIPPET: 'kickstart_start'
# LAUNCHES %pre TRIGGERS IF THOSE INSTALLED

wget "http://10.20.0.2/cblr/svc/op/trig/mode/pre/system/node3" -O /dev/null

# COBBLER EMBEDDED SNIPPET: 'pre_install_network_config'
# PRECONFIGURES NETWORK INTERFACES DEPENDING ON
# COBBLER SYSTEM PARAMETERS
# IN PARTICULAR IT WRITES KICKSTART NETWORK CONFIGURATION
# INTO /tmp/pre_install_network_config WHICH IS INCLUDED
# INTO KICKSTART BY 'network_config' SNIPPET
# Start pre_install_network_config generated code

# Start of code to match cobbler system interfaces to physical interfaces by their mac addresses
#  Start eth2
# Configuring eth2 (00:0c:29:27:68:55)
if ifconfig -a | grep -i 00:0c:29:27:68:55
then
  IFNAME=$(ifconfig -a | grep -i '00:0c:29:27:68:55' | cut -d " " -f 1)
  echo "network --noipv6 --device=$IFNAME --bootproto=dhcp --hostname=node3.domain.tld" >> /tmp/pre_install_network_config
fi
#  Start eth1
# Configuring eth1 (00:0c:29:27:68:4b)
if ifconfig -a | grep -i 00:0c:29:27:68:4b
then
  IFNAME=$(ifconfig -a | grep -i '00:0c:29:27:68:4b' | cut -d " " -f 1)
  echo "network --noipv6 --device=$IFNAME --bootproto=dhcp --hostname=node3.domain.tld" >> /tmp/pre_install_network_config
fi
#  Start eth0
# Configuring eth0 (00:0c:29:27:68:41)
if ifconfig -a | grep -i 00:0c:29:27:68:41
then
  IFNAME=$(ifconfig -a | grep -i '00:0c:29:27:68:41' | cut -d " " -f 1)
  echo "network --noipv6 --device=$IFNAME --bootproto=dhcp --hostname=node3.domain.tld" >> /tmp/pre_install_network_config
fi
# End pre_install_network_config generated code


# CONFIGURES SSH KEY ACCESS FOR SSHD CONSOLE
# DURING OPERATING SYSTEM INSTALLATION
mkdir -p --mode=700 /root/.ssh
cat > /root/.ssh/authorized_keys2 <<EOF
ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA2THOacfRJLpUVVlthvJOJjVYZNq3uCaNw0JUmyhB3jKWS8dVcemPUHPvSXKDO+9xpf0UwxlWmtdSNn+s5k9Tk0lrUOOBDB2Zw4jNQaaO9ivLyLMcaaYn2/qSs+nK+Th4Km2Jpg/glj40JQkWXPiguhSrm6ZEjSnkH6Xe9uQFGaFA9K2x7ycWto79URvFbQhkg9DXYfrAv7vyi7E53Pt89ZibZ9S2r0Qs/vhBbgUmizSK6Cdotg/cmpqMn6KctGrbybjjD+5QTRlWX6aiJkL/m/bWcX+X+IZcINUcalyhbsQuB88Asl79E9DgP94wYtuY01vSgCF1xtjSiVw3h3W5DQ== root@fuel.domain.tld

EOF
chmod 600 /root/.ssh/authorized_keys2


# COBBLER EMBEDDED SNIPPET: 'pre_install_partition'
# DETECTS HARD DRIVES AND SETS FIRST OF THEM
# AS INSTALLATION TARGET AND BOOTLOADER INSTALLATION TARGET
hdparm -z $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) )
test -e $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) ) && dd if=/dev/zero of=$(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) ) bs=1M count=10
sleep 10
hdparm -z $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) )
parted -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) ) mklabel gpt
parted -a none -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) ) unit MiB mkpart primary 0 24
parted -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) ) set 1 bios_grub on
parted -a none -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) ) unit MiB mkpart primary fat32 24 224
parted -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) ) set 2 boot on
hdparm -z $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:1:0) 2>/dev/null) )
test -e $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:1:0) 2>/dev/null) ) && dd if=/dev/zero of=$(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:1:0) 2>/dev/null) ) bs=1M count=10
sleep 10
hdparm -z $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:1:0) 2>/dev/null) )
parted -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:1:0) 2>/dev/null) ) mklabel gpt
parted -a none -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:1:0) 2>/dev/null) ) unit MiB mkpart primary 0 24
parted -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:1:0) 2>/dev/null) ) set 1 bios_grub on
parted -a none -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:1:0) 2>/dev/null) ) unit MiB mkpart primary fat32 24 224
parted -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:1:0) 2>/dev/null) ) set 2 boot on
hdparm -z $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:2:0) 2>/dev/null) )
test -e $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:2:0) 2>/dev/null) ) && dd if=/dev/zero of=$(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:2:0) 2>/dev/null) ) bs=1M count=10
sleep 10
hdparm -z $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:2:0) 2>/dev/null) )
parted -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:2:0) 2>/dev/null) ) mklabel gpt
parted -a none -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:2:0) 2>/dev/null) ) unit MiB mkpart primary 0 24
parted -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:2:0) 2>/dev/null) ) set 1 bios_grub on
parted -a none -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:2:0) 2>/dev/null) ) unit MiB mkpart primary fat32 24 224
parted -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:2:0) 2>/dev/null) ) set 2 boot on
parted -a none -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) ) unit MiB mkpart primary 224 724
parted -a none -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) ) unit MiB mkpart primary 724 18196
parted -a none -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) ) unit MiB mkpart primary 18196 20404
parted -a none -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:1:0) 2>/dev/null) ) unit MiB mkpart primary 224 20340
parted -a none -s $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:2:0) 2>/dev/null) ) unit MiB mkpart primary 224 20340
sleep 10
hdparm -z $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) )
hdparm -z $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:1:0) 2>/dev/null) )
hdparm -z $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:2:0) 2>/dev/null) )
for v in $(vgs | awk '{print $1}'); do vgreduce -f --removemissing $v; vgremove -f $v; done
for p in $(pvs | grep '\/dev' | awk '{print $1}'); do pvremove -ff -y $p ; done
mdadm --zero-superblock --force $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) )*
mdadm --zero-superblock --force $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:1:0) 2>/dev/null) )*
mdadm --zero-superblock --force $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:2:0) 2>/dev/null) )*
echo > /tmp/partition.ks
echo "partition /boot --onpart=$(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) )3" >> /tmp/partition.ks
echo "partition pv.001 --onpart=$(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) )4" >> /tmp/partition.ks
echo "partition pv.002 --onpart=$(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) )5" >> /tmp/partition.ks
echo "partition pv.003 --onpart=$(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:1:0) 2>/dev/null) )3" >> /tmp/partition.ks
echo "partition pv.004 --onpart=$(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:2:0) 2>/dev/null) )3" >> /tmp/partition.ks
echo "volgroup soft pv.002 pv.003 pv.004" >> /tmp/partition.ks
echo "volgroup os pv.001" >> /tmp/partition.ks
echo "logvol / --vgname=os --size=15360 --name=root --fstype=ext4" >> /tmp/partition.ks
echo "logvol swap --vgname=os --size=2048 --name=swap " >> /tmp/partition.ks
echo "bootloader --location=mbr --driveorder=$(basename $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) )),$(basename $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:1:0) 2>/dev/null) )),$(basename $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:2:0) 2>/dev/null) )) --append=' console=ttyS0,9600 console=tty0 biosdevname=0 crashkernel=none rootdelay=90 nomodeset '" >> /tmp/partition.ks
echo "%post --nochroot" > /tmp/post_partition.ks
echo "set -x -v" >> /tmp/post_partition.ks
echo "exec 1>/mnt/sysimage/root/post-partition.log 2>&1" >> /tmp/post_partition.ks
echo "lvcreate --size 42248 --name soft soft" >> /tmp/post_partition.ks
echo "mkfs.xfs -f -s size=512 /dev/mapper/soft-soft" >> /tmp/post_partition.ks
echo "mkdir -p /mnt/sysimage/apps" >> /tmp/post_partition.ks
echo "echo '/dev/mapper/soft-soft /apps xfs defaults 0 0' >> /mnt/sysimage/etc/fstab" >> /tmp/post_partition.ks
echo "echo -n > /tmp/grub.script" >> /tmp/post_partition.ks
echo "echo \"device (hd0) /dev/$(basename $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:0:0) 2>/dev/null) ))\" >> /tmp/grub.script" >> /tmp/post_partition.ks
echo "echo \"geometry (hd0) 130 255 63\" >> /tmp/grub.script" >> /tmp/post_partition.ks
echo "echo \"root (hd0,2)\" >> /tmp/grub.script" >> /tmp/post_partition.ks
echo "echo \"install /grub/stage1 (hd0) /grub/stage2 p /grub/grub.conf\" >> /tmp/grub.script" >> /tmp/post_partition.ks
echo "echo quit >> /tmp/grub.script" >> /tmp/post_partition.ks
echo "cat /tmp/grub.script | chroot /mnt/sysimage /sbin/grub --no-floppy --batch" >> /tmp/post_partition.ks
echo "echo -n > /tmp/grub.script" >> /tmp/post_partition.ks
echo "echo \"device (hd0) /dev/$(basename $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:1:0) 2>/dev/null) ))\" >> /tmp/grub.script" >> /tmp/post_partition.ks
echo "echo \"geometry (hd0) 130 255 63\" >> /tmp/grub.script" >> /tmp/post_partition.ks
echo "echo \"root (hd0,2)\" >> /tmp/grub.script" >> /tmp/post_partition.ks
echo "echo \"install /grub/stage1 (hd0) /grub/stage2 p /grub/grub.conf\" >> /tmp/grub.script" >> /tmp/post_partition.ks
echo "echo quit >> /tmp/grub.script" >> /tmp/post_partition.ks
echo "cat /tmp/grub.script | chroot /mnt/sysimage /sbin/grub --no-floppy --batch" >> /tmp/post_partition.ks
echo "echo -n > /tmp/grub.script" >> /tmp/post_partition.ks
echo "echo \"device (hd0) /dev/$(basename $(readlink -f $( (ls /dev/disk/by-path/pci-0000:00:10.0-scsi-0:0:2:0) 2>/dev/null) ))\" >> /tmp/grub.script" >> /tmp/post_partition.ks
echo "echo \"geometry (hd0) 130 255 63\" >> /tmp/grub.script" >> /tmp/post_partition.ks
echo "echo \"root (hd0,2)\" >> /tmp/grub.script" >> /tmp/post_partition.ks
echo "echo \"install /grub/stage1 (hd0) /grub/stage2 p /grub/grub.conf\" >> /tmp/grub.script" >> /tmp/post_partition.ks
echo "echo quit >> /tmp/grub.script" >> /tmp/post_partition.ks
echo "cat /tmp/grub.script | chroot /mnt/sysimage /sbin/grub --no-floppy --batch" >> /tmp/post_partition.ks
echo "%end" >> /tmp/post_partition.ks



# CONFIGURE ANACONDA YUM SETTINGS
# Error: no snippet data for anaconda-yum


# PACKAGES SECTION
# HERE ARE LIST OF PACKAGES THAT WILL BE INSTALLED
# FIXME --ignoremissing
%packages --nobase --ignoremissing

@Core
authconfig
bfa-firmware
bind-utils
cronie
crontabs
curl
daemonize
gcc
gdisk
make
mlocate
nailgun-agent
nailgun-mcagents
nailgun-net-check
nmap-ncat
ntp
openssh
openssh-clients
openssh-server
perl
ql2100-firmware
ql2200-firmware
ql23xx-firmware
ql2400-firmware
ql2500-firmware
rhn-setup
rsync
ruby-augeas
ruby-devel
rubygem-openstack
rubygem-netaddr
system-config-firewall-base
tcpdump
telnet
virt-what
vim
wget
yum
yum-utils

# COBBLER EMBEDDED SNIPPET: 'centos_ofed_prereq_pkgs_if_enabled'
# LISTS ofed prereq PACKAGES IF mlnx_plugin_mode VARIABLE IS SET TO enabled



# COBBLER EMBEDDED SNIPPET: 'puppet_install_if_enabled'
# LISTS puppet PACKAGE IF puppet_auto_setup VARIABLE IS SET TO 1
puppet


# COBBLER EMBEDDED SNIPPET: 'mcollective_install_if_enabled'
# LISTS mcollective PACKAGE IF mco_auto_setup VARIABLE IS SET TO 1
mcollective


# POST INSTALLATION PARTITIONING
# THERE ARE SOME COMMANDS TO CREATE LARGE (>1TB) VOLUMES
# AND INSTALL GRUB BOOTLOADER TO MAKE NODES ABLE TO BOOT FROM ANY HARDDRIVE
%include /tmp/post_partition.ks

# POSTINSTALL SECTION
# HERE ARE COMMANDS THAT WILL BE LAUNCHED JUST AFTER
# INSTALLATION ITSELF COMPLETED
%post

yum-config-manager --disableplugin=fastestmirror --save &>/dev/null

echo -e "modprobe nf_conntrack_ipv4\nmodprobe nf_conntrack_ipv6" >> /etc/rc.modules
chmod +x /etc/rc.modules
echo -e "net.nf_conntrack_max=1048576" >> /etc/sysctl.conf
mkdir -p /var/log/coredump
echo -e "kernel.core_pattern=/var/log/coredump/core.%e.%p.%h.%t" >> /etc/sysctl.conf
chmod 777 /var/log/coredump
echo -e "* soft core unlimited\n* hard core unlimited" >> /etc/security/limits.conf
sed -i '/\*.*soft.*nproc.*1024$/s/1024/10240/' /etc/security/limits.d/90-nproc.conf

# COBBLER EMBEDDED SNIPPET: 'log_ks_post'
# CONFIGURES %post LOGGING
set -x -v
exec 1>/root/ks-post.log 2>&1


# COBBLER EMBEDDED SNIPPET: 'post_install_kernel_options'
# CONFIGURES KERNEL PARAMETERS ON INSTALLED SYSTEM




# COBBLER EMBEDDED SNIPPET: 'post_install_network_config'
# CONFIGURES NETWORK INTERFACES DEPENDING ON
# COBBLER SYSTEM PARAMETERS
# Start post_install_network_config generated code

# create a working directory for interface scripts
mkdir /etc/sysconfig/network-scripts/cobbler
cp /etc/sysconfig/network-scripts/ifcfg-lo /etc/sysconfig/network-scripts/cobbler/

# set the hostname in the network configuration file
grep -v HOSTNAME /etc/sysconfig/network > /etc/sysconfig/network.cobbler
echo "HOSTNAME=node3.domain.tld" >> /etc/sysconfig/network.cobbler
rm -f /etc/sysconfig/network
mv /etc/sysconfig/network.cobbler /etc/sysconfig/network

# Also set the hostname now, some applications require it
# (e.g.: if we're connecting to Puppet before a reboot).
/bin/hostname node3.domain.tld

# Start configuration for eth2


echo "DEVICE=eth2" > /etc/sysconfig/network-scripts/cobbler/ifcfg-eth2
echo "HWADDR=00:0C:29:27:68:55" >> /etc/sysconfig/network-scripts/cobbler/ifcfg-eth2
IFNAME=$(ifconfig -a | grep -i '00:0C:29:27:68:55' | cut -d ' ' -f 1)
if [ -f "/etc/modprobe.conf" ] && [ $IFNAME ]; then
    grep $IFNAME /etc/modprobe.conf | sed "s/$IFNAME/eth2/" >> /etc/modprobe.conf.cobbler
    grep -v $IFNAME /etc/modprobe.conf >> /etc/modprobe.conf.new
    rm -f /etc/modprobe.conf
    mv /etc/modprobe.conf.new /etc/modprobe.conf
fi
echo "TYPE=Ethernet" >> /etc/sysconfig/network-scripts/cobbler/ifcfg-eth2
echo "BOOTPROTO=none" >> /etc/sysconfig/network-scripts/cobbler/ifcfg-eth2
echo "DNS1=10.20.0.2" >> /etc/sysconfig/network-scripts/cobbler/ifcfg-eth2
# End configuration for eth2

# Start configuration for eth1


echo "DEVICE=eth1" > /etc/sysconfig/network-scripts/cobbler/ifcfg-eth1
echo "HWADDR=00:0C:29:27:68:4B" >> /etc/sysconfig/network-scripts/cobbler/ifcfg-eth1
IFNAME=$(ifconfig -a | grep -i '00:0C:29:27:68:4B' | cut -d ' ' -f 1)
if [ -f "/etc/modprobe.conf" ] && [ $IFNAME ]; then
    grep $IFNAME /etc/modprobe.conf | sed "s/$IFNAME/eth1/" >> /etc/modprobe.conf.cobbler
    grep -v $IFNAME /etc/modprobe.conf >> /etc/modprobe.conf.new
    rm -f /etc/modprobe.conf
    mv /etc/modprobe.conf.new /etc/modprobe.conf
fi
echo "TYPE=Ethernet" >> /etc/sysconfig/network-scripts/cobbler/ifcfg-eth1
echo "BOOTPROTO=none" >> /etc/sysconfig/network-scripts/cobbler/ifcfg-eth1
echo "DNS1=10.20.0.2" >> /etc/sysconfig/network-scripts/cobbler/ifcfg-eth1
# End configuration for eth1

# Start configuration for eth0


echo "DEVICE=eth0" > /etc/sysconfig/network-scripts/cobbler/ifcfg-eth0
echo "HWADDR=00:0C:29:27:68:41" >> /etc/sysconfig/network-scripts/cobbler/ifcfg-eth0
IFNAME=$(ifconfig -a | grep -i '00:0C:29:27:68:41' | cut -d ' ' -f 1)
if [ -f "/etc/modprobe.conf" ] && [ $IFNAME ]; then
    grep $IFNAME /etc/modprobe.conf | sed "s/$IFNAME/eth0/" >> /etc/modprobe.conf.cobbler
    grep -v $IFNAME /etc/modprobe.conf >> /etc/modprobe.conf.new
    rm -f /etc/modprobe.conf
    mv /etc/modprobe.conf.new /etc/modprobe.conf
fi
echo "TYPE=Ethernet" >> /etc/sysconfig/network-scripts/cobbler/ifcfg-eth0
echo "BOOTPROTO=none" >> /etc/sysconfig/network-scripts/cobbler/ifcfg-eth0
echo "DNS1=10.20.0.2" >> /etc/sysconfig/network-scripts/cobbler/ifcfg-eth0
# End configuration for eth0

sed -i -e "/^search /d" /etc/resolv.conf
echo -n "search " >>/etc/resolv.conf
echo -n "domain.tld " >>/etc/resolv.conf
echo "" >>/etc/resolv.conf

sed -i -e "/^nameserver /d" /etc/resolv.conf
echo "nameserver 10.20.0.2" >>/etc/resolv.conf

sed -i 's/ONBOOT=yes/ONBOOT=no/g' /etc/sysconfig/network-scripts/ifcfg-eth*

rm -f /etc/sysconfig/network-scripts/ifcfg-*
mv /etc/sysconfig/network-scripts/cobbler/* /etc/sysconfig/network-scripts/
rm -r /etc/sysconfig/network-scripts/cobbler
if [ -f "/etc/modprobe.conf" ]; then
cat /etc/modprobe.conf.cobbler >> /etc/modprobe.conf
rm -f /etc/modprobe.conf.cobbler
fi
# End post_install_network_config generated code


# COBBLER EMBEDDED SNIPPET: 'puppet_conf'
# CONFIGURES PUPPET AGENT
mkdir -p /etc/puppet /var/lib/hiera
touch /var/lib/hiera/common.yaml /etc/puppet/hiera.yaml
cat <<EOCONF > /etc/puppet/puppet.conf
[main]
    # The Puppet log directory.
    # The default value is '\$vardir/log'.
    logdir = /var/log/puppet

    # Where Puppet PID files are kept.
    # The default value is '\$vardir/run'.
    rundir = /var/run/puppet

    # Where SSL certificates are kept.
    # The default value is '\$confdir/ssl'.
    ssldir = \$vardir/ssl
    pluginsync = true
[agent]
    # The file in which puppetd stores a list of the classes
    # associated with the retrieved configuratiion.  Can be loaded in
    # the separate ``puppet`` executable using the ``--loadclasses``
    # option.
    # The default value is '\$confdir/classes.txt'.
    classfile = \$vardir/classes.txt

    # Where puppetd caches the local configuration.  An
    # extension indicating the cache format is added automatically.
    # The default value is '\$confdir/localconfig'.
    localconfig = \$vardir/localconfig
    server = fuel.domain.tld
    # How long the client should wait for the configuration to be retrieved before considering it a failure.
    # It may help with 'execution expired' issue we've experienced.
    configtimeout = 600
    # Don't send reports after every run.
    report = false

EOCONF


# COBBLER EMBEDDED SNIPPET: 'puppet_register_if_enabled'
# CREATES CERTIFICATE REQUEST AND SENDS IT TO PUPPET MASTER


# COBBLER EMBEDDED SNIPPET: 'mcollective_conf'
# CONFIGURES MCOLLECTIVE AGENT
mkdir -p /etc/mcollective
cat <<EOCONF > /etc/mcollective/server.cfg
main_collective = mcollective
collectives = mcollective
libdir = /usr/libexec/mcollective
logfile = /var/log/mcollective.log
loglevel = debug
daemonize = 1
direct_addressing = 1

# Set huge value of ttl to avoid cases with unsyncronized time between nodes
# It means that ttl approximately equal to 50 days
ttl = 4294957

# Plugins
securityprovider = psk
plugin.psk = unset

connector = rabbitmq
plugin.rabbitmq.vhost = mcollective
plugin.rabbitmq.pool.size = 1
plugin.rabbitmq.pool.1.host = 10.20.0.2
plugin.rabbitmq.pool.1.port = $mco_port
plugin.rabbitmq.pool.1.user = mcollective
plugin.rabbitmq.pool.1.password = 6CjcVMEV
plugin.rabbitmq.heartbeat_interval = 30


# Facts
factsource = yaml
plugin.yaml = /etc/mcollective/facts.yaml
EOCONF

# turn on mcollective service after reboot and set priority to 81
sed -i /etc/rc.d/init.d/mcollective -e 's/\(# chkconfig:\s\+[-0-6]\+\) [0-9]\+ \([0-9]\+\)/\1 81 \2/'
/sbin/chkconfig mcollective on


# SNIPPET: 'kickstart_ntp'
# SYNC LOCAL TIME VIA NTP
ntpdate -t 4 -b 10.20.0.2
hwclock --systohc


# SNIPPET: 'ntp_to_masternode'
# CONFIGURES NTPD POOL TO MASTER NODE
# Disable panic about huge clock offset
sed -i '/^\s*tinker panic/ d' /etc/ntp.conf
sed -i '1 i tinker panic 0' /etc/ntp.conf

echo 0 > /var/lib/ntp/drift
chown ntp: /var/lib/ntp/drift

# Point installed ntpd to Master node
sed -i '/^\s*server/ d' /etc/ntp.conf
echo "server 10.20.0.2 burst iburst" >> /etc/ntp.conf
sed -i 's/SYNC_HWCLOCK\s*=\s*no/SYNC_HWCLOCK=yes/' /etc/sysconfig/ntpdate
chkconfig ntpd on
chkconfig ntpdate on


# Let's not to use separate snippet for just one line of code. Complexity eats my time.
echo 'flock -w 0 -o /var/lock/agent.lock -c "/opt/nailgun/bin/agent >> /var/log/nailgun-agent.log 2>&1"' >> /etc/rc.local

# It is for the internal nailgun using
echo target > /etc/nailgun_systemtype

# COBBLER EMBEDDED SNIPPET: 'authorized_keys'
# PUTS authorized_keys file into /root/.ssh/authorized_keys
mkdir -p /root/.ssh
chown root:root /root/.ssh
chmod 700 /root/.ssh
cat > /root/.ssh/authorized_keys <<EOF
ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA2THOacfRJLpUVVlthvJOJjVYZNq3uCaNw0JUmyhB3jKWS8dVcemPUHPvSXKDO+9xpf0UwxlWmtdSNn+s5k9Tk0lrUOOBDB2Zw4jNQaaO9ivLyLMcaaYn2/qSs+nK+Th4Km2Jpg/glj40JQkWXPiguhSrm6ZEjSnkH6Xe9uQFGaFA9K2x7ycWto79URvFbQhkg9DXYfrAv7vyi7E53Pt89ZibZ9S2r0Qs/vhBbgUmizSK6Cdotg/cmpqMn6KctGrbybjjD+5QTRlWX6aiJkL/m/bWcX+X+IZcINUcalyhbsQuB88Asl79E9DgP94wYtuY01vSgCF1xtjSiVw3h3W5DQ== root@fuel.domain.tld


EOF
chown root:root /root/.ssh/authorized_keys


# COBBLER EMBEDDED SNIPPET: 'nailgun_repo'
# REMOVES ALL *.repo FILES FROM /etc/yum.repos.d AND
# CREATES /etc/yum.repos.d/nailgun.repo FILE AND
# PUTS IN IT ALL THE REPOSITORIES DEFINED IN ks_repo VARIABLE
rm /etc/yum.repos.d/*.repo
cat > /etc/yum.repos.d/nailgun.repo << EOF

# REPOSITORIES FROM Nailgun
[2014.2-6.0]
name=2014.2-6.0
baseurl=http://10.20.0.2:8080/2014.2-6.0/centos/x86_64
gpgcheck=0
EOF

rpm -e --nodeps ruby
yum install --exclude=ruby-2.1.1* -y ruby rubygems
yum update -y --exclude --exclude=ruby*

mkdir -p /etc/nailgun-agent/
cat > /etc/nailgun-agent/config.yaml << EOA
---
url: 'http://10.20.0.2:8000/api'
EOA

# COBBLER EMBEDDED SNIPPET: 'kernel_lt_if_enabled'
# INSTALLS kernel-lt PACKAGE IF kernel_lt VARIABLE IS SET TO 1


# COBBLER EMBEDDED SNIPPET: 'ssh_disable_gssapi'
# REMOVES "GSSAPICleanupCredentials yes" AND "GSSAPIAuthentication yes" LINES
# FROM /etc/ssh/sshd_config
sed -i -e "/^\s*GSSAPICleanupCredentials yes/d" -e "/^\s*GSSAPIAuthentication yes/d" /etc/ssh/sshd_config


# COBBLER EMBEDDED SNIPPET: 'redhat_register'
# REGISTER AT REDHAT WITH ACTIVATION KEY
# begin Red Hat management server registration
# not configured to register to any Red Hat management server (ok)
# end Red Hat management server registration



# REGISTER TO RED HAT SUBSCRIPTION MANAGER WITH LOGIN/PASSWORD
# begin Red Hat Network certificate-based server registration

# not configured to use Certificate-based RHN (ok)
# end Red Hat Network certificate-based server registration



# Let's not wait forewer when ssh'ing:
sed -i --follow-symlinks -e '/UseDNS/d' /etc/ssh/sshd_config
echo 'UseDNS no' >> /etc/ssh/sshd_config

# COBBLER EMBEDDED SNIPPET: 'sshd_auth_pubkey_only'
# DISABLE PASSWORD AUTH. ALLOW PUBKEY AUTH ONLY IN /etc/ssh/sshd_config
# Allow ssh auth PubKey only.
sed --follow-symlinks -i 's/^\s*PubkeyAuthentication\s+no/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed --follow-symlinks -i '/^\s*PasswordAuthentication/d' /etc/ssh/sshd_config
echo 'PasswordAuthentication no' >> /etc/ssh/sshd_config


# Copying default bash settings to the root directory
cp -f /etc/skel/.bash* /root/

# Rsyslogd should send all messages to master node
cat >/etc/rsyslog.d/10-log2master.conf <<EOF
# Log all messages to master node
\$template LogToMaster, "<%PRI%>1 %\$NOW%T%TIMESTAMP:8:\$%Z %HOSTNAME% %APP-NAME% %PROCID% %MSGID% -%msg%\n"
*.* @10.20.0.2;LogToMaster
EOF

# Configure static IP address for admin interface
#!/bin/bash
DEFAULT_GW=10.20.0.2
ADMIN_MAC=$(sed 's/\ /\n/g' /proc/cmdline | grep choose_interface | awk -F\= '{print $2}')
ADMIN_IF=$(tr ' ' '\n' < /proc/cmdline | grep "udevrules=" | sed 's/[,=]/\n/g' | grep "$ADMIN_MAC" | cut -d_ -f2 | head -1)
INSTALL_IF=$(ifconfig | grep "$ADMIN_MAC" | head -1 | cut -d' ' -f1)
NETADDR=( $(ifconfig $INSTALL_IF | grep -oP "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}") )
echo -e "# FROM COBBLER SNIPPET\nDEVICE=$ADMIN_IF\nIPADDR=${NETADDR[0]}\nNETMASK=${NETADDR[2]}\nBOOTPROTO=none\nONBOOT=yes\nUSERCTL=no\n" > /etc/sysconfig/network-scripts/ifcfg-"$ADMIN_IF"

echo GATEWAY="$DEFAULT_GW" >> /etc/sysconfig/network

cat /proc/cmdline | tr ' ' '\n' | grep udevrules | tr '[:upper:]' '[:lower:]' | sed -e 's/udevrules=//g' -e 's/,/\n/g' | sed -e "s/^/SUBSYSTEM==\"net\",\ ACTION==\"add\",\ DRIVERS==\"?*\",\ ATTR{address}==\"/g" -e "s/_/\",\ ATTR{type}==\"1\",\ KERNEL==\"eth*\",\ NAME=\"/g" -e "s/$/\"/g" | tee /etc/udev/rules.d/70-persistent-net.rules


# Blacklist i2c_piix4 module so it does not create kernel errors
[[ $(virt-what) = "virtualbox" ]] && echo "blacklist i2c_piix4" >> /etc/modprobe.d/blacklist-i2c_piix4.conf


# Install OFED components for RDMA if needed



# COBBLER EMBEDDED SNIPPET: 'kickstart_done'
# DISABLES PXE BOOTING

wget "http://10.20.0.2/cblr/svc/op/ks/system/node3" -O /root/cobbler.ks
wget "http://10.20.0.2/cblr/svc/op/trig/mode/post/system/node3" -O /dev/null
wget "http://10.20.0.2/cblr/svc/op/nopxe/system/node3" -O /dev/null

%end
