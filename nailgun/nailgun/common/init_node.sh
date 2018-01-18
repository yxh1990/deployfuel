master_ip=10.20.0.0
puppet_master=fuel.domain.tld
mco_password=111
#mco_port=61613



######nailgun repo ##############
rm -fr /etc/yum.repos.d/*.repo
cat > /etc/yum.repos.d/nailgun.repo <<EOF
[2014.2-6.0]
name = 2014.2-6.0
baseurl = http://${master_ip}:8080/2014.2-6.0/centos/bclinux7.2
gpgcheck=0
EOF

mkdir -p /etc/nailgun-agent/
cat > /etc/nailgun-agent/config.yaml <<EOF
url: "http://${master_ip}:8000/api"
EOF

yum clean all
yum -y install authconfig bind-utils cronie crontabs curl gcc gdisk make mlocate nmap-ncat ntp openssh openssh-clients openssh-server perl rsync
yum -y install system-config-firewall-base tcpdump telnet virt-what vim parted expect puppet
yum -y install bfa-firmware daemonize libselinux-ruby ruby ruby-augeas ruby-devel rubygem-netaddr ruby21-rubygem-openstack rubygem-cstruct rubygem-mixlib-log rubygem-mixlib-config rubygem-mixlib-cli rubygem-yajl-ruby nailgun-mcagents nailgun-net-check

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
plugin.rabbitmq.pool.1.port = 
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


# COBBLER EMBEDDED SNIPPET: 'authorized_keys'
# PUTS authorized_keys file into /root/.ssh/authorized_keys

# Copying default bash settings to the root directory
cp -f /etc/skel/.bash* /root/
# COBBLER EMBEDDED SNIPPET: 'ssh_disable_gssapi'
# REMOVES "GSSAPICleanupCredentials yes" AND "GSSAPIAuthentication yes" LINES
# FROM /etc/ssh/sshd_config


setenforce 0 
sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config

#service iptables stop
#chkconfig iptables off


systemctl stop firewalld.service #停止firewall
systemctl disable firewalld.service #禁止firewall开机启动

echo True > /root/initnode_res



echo 'flock -w 60 -o /var/lock/nailgun-agent.lock -c "/usr/bin/nailgun-agent >> /var/log/nailgun-agent.log 2>&1"' >> /etc/rc.local
echo '* * * * * root flock -w 60 -o /var/lock/nailgun-agent.lock -c "/usr/bin/nailgun-agent 2>&1 | tee -a /var/log/nailgun-agent.log  | /usr/bin/logger -t nailgun-agent"' > /etc/cron.d/nailgun-agent
sed -i "s/::File.read(\"\/proc\/cmdline\")/YAML.load_file(AGENT_CONFIG)['url']/" /usr/bin/nailgun-agent

# It is for the internal nailgun using
echo target > /etc/nailgun_systemtype

echo "the script is success end...."
