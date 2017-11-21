master_ip=10.20.0.2
eth_name=eth1
pxe_ip=10.20.0.4
netmask=255.255.255.0
puppet_master=fuel.domain.tld
mco_password=6CjcVMEV
mco_port=61613
rpm_url=http://${master_ip}:8080/2014.2-6.0/centos/x86_64/Packages

rm -f /etc/sysconfig/network-scripts/ifcfg-${eth_name}
cat > /etc/sysconfig/network-scripts/ifcfg-${eth_name} <<EOF
DEVICE=${eth_name}
BOOTPROTO=none
ONBOOT=yes
USERCTL=no
IPADDR=${pxe_ip}
NETMASK=${netmask}
EOF

echo "restarting the pxe networking......"
#systemctl restart network
ifconfig ${eth_name} down && ifconfig ${eth_name} up
echo "the pxe network is available"


######nailgun repo ##############
rm /etc/yum.repos.d/*.repo
cat > /etc/yum.repos.d/nailgun.repo <<EOF
[2014.2-6.0]
name = 2014.2-6.0
baseurl = http://${master_ip}:8080/2014.2-6.0/centos/x86_64
gpgcheck=0
EOF

mkdir -p /etc/nailgun-agent/
cat > /etc/nailgun-agent/config.yaml <<EOF
url: "http://${master_ip}:8000/api"
EOF


yum clean all
yum -y install ruby
rpm -e --nodeps ruby
yum install --exclude=ruby-2.1.1* -y ruby rubygems
yum update -y --exclude --exclude=ruby*

yum -y install authconfig bfa-firmware bind-utils cronie crontabs curl daemonize gcc gdisk make mcollective
yum -y install mlocate nailgun-agent nailgun-mcagents nailgun-net-check nmap-ncat ntp openssh openssh-clients openssh-server
yum -y install perl puppet ql2100-firmware ql2200-firmware ql23xx-firmware ql2400-firmware ql2500-firmware
yum -y install rhn-setup rsync ruby-augeas ruby-devel rubygem-netaddr rubygem-openstack system-config-firewall-base
yum -y install tcpdump telnet vim virt-what wget

########### mcollective_conf ###########
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
plugin.rabbitmq.pool.1.host = ${master_ip}
plugin.rabbitmq.pool.1.port = ${mco_port}
plugin.rabbitmq.pool.1.user = mcollective
plugin.rabbitmq.pool.1.password = ${mco_password}
plugin.rabbitmq.heartbeat_interval = 30


# Facts
factsource = yaml
plugin.yaml = /etc/mcollective/facts.yaml
EOCONF
# turn on mcollective service after reboot and set priority to 81
sed -i /etc/rc.d/init.d/mcollective -e 's/\(# chkconfig:\s\+[-0-6]\+\) [0-9]\+ \([0-9]\+\)/\1 81 \2/'
/sbin/chkconfig mcollective on
/etc/rc.d/init.d/mcollective start
# Let's not to use separate snippet for just one line of code. Complexity eats my time.
chmod +x /etc/rc.d/rc.local
echo 'flock -w 60 -o /var/lock/nailgun-agent.lock -c "/opt/nailgun/bin/agent >> /var/log/nailgun-agent.log 2>&1"' >> /etc/rc.local
echo '* * * * * root flock -w 60 -o /var/lock/nailgun-agent.lock -c "/opt/nailgun/bin/agent 2>&1 | tee -a /var/log/nailgun-agent.log  | /usr/bin/logger -t nailgun-agent"' > /etc/cron.d/nailgun-agent
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
chmod 600 /root/.ssh/authorized_keys
chown root:root /root/.ssh/authorized_keys
# Copying default bash settings to the root directory
cp -f /etc/skel/.bash* /root/
# COBBLER EMBEDDED SNIPPET: 'ssh_disable_gssapi'
# REMOVES "GSSAPICleanupCredentials yes" AND "GSSAPIAuthentication yes" LINES
# FROM /etc/ssh/sshd_config
sed -i -e "/^\s*GSSAPICleanupCredentials yes/d" -e "/^\s*GSSAPIAuthentication yes/d" /etc/ssh/sshd_config
# Let's not wait forewer when ssh'ing:
sed -i --follow-symlinks -e '/UseDNS/d' /etc/ssh/sshd_config
echo 'UseDNS no' >> /etc/ssh/sshd_config

sed -i "s/::File.read(\"\/proc\/cmdline\")/YAML.load_file(AGENT_CONFIG)['url']/" /opt/nailgun/bin/agent


setenforce 0 
sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config

service iptables stop
chkconfig iptables off

#systemctl stop firewalld.service #停止firewall
#systemctl disable firewalld.service #禁止firewall开机启动

#echo "api_ip: ${master_ip}" >> /etc/nailgun-agent/config.yaml
echo "the script is completed execution........................"
