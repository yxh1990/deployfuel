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

########### ruby env ###########
rpm -i ${rpm_url}/compat-readline5-5.2-17.1.el6.x86_64.rpm
rpm -i ${rpm_url}/ruby-libs-1.8.7.352-13.el6.x86_64.rpm
rpm -i ${rpm_url}/ruby-1.8.7.352-13.el6.x86_64.rpm
rpm -i ${rpm_url}/ruby-irb-1.8.7.352-13.el6.x86_64.rpm
rpm -i ${rpm_url}/libselinux-ruby-2.0.94-5.3.el6_4.1.x86_64.rpm
rpm -i ${rpm_url}/ruby-shadow-1.4.1-13.el6.x86_64.rpm
rpm -i ${rpm_url}/ruby-rdoc-1.8.7.352-13.el6.x86_64.rpm
rpm -i ${rpm_url}/augeas-libs-1.0.0-5.mira1.x86_64.rpm
rpm -i ${rpm_url}/ruby-augeas-0.5.0-17.3.x86_64.rpm
rpm -i ${rpm_url}/ruby-rgen-0.6.5-1.el6.noarch.rpm
rpm -i ${rpm_url}/rubygems-1.3.7-5.el6.noarch.rpm
rpm -i ${rpm_url}/rubygem-mixlib-cli-1.2.2-3.el6.noarch.rpm
rpm -i ${rpm_url}/rubygem-json-1.7.7-101.el6.x86_64.rpm
rpm -i ${rpm_url}/rubygem-httpclient-2.3.2-5.el6.noarch.rpm
rpm -i ${rpm_url}/rubygem-stomp-1.2.16-1.el6.noarch.rpm
rpm -i ${rpm_url}/rubygem-mixlib-log-1.4.1-1.el6.noarch.rpm
rpm -i ${rpm_url}/rubygem-systemu-2.5.2-1.el6.noarch.rpm
rpm -i ${rpm_url}/rubygem-cstruct-1.0.1-1.el6.noarch.rpm
rpm -i ${rpm_url}/rubygem-rethtool-0.0.3-2.mira1.noarch.rpm
rpm -i ${rpm_url}/rubygem-extlib-0.9.13-5.el6.noarch.rpm
rpm -i ${rpm_url}/rubygem-mixlib-config-1.1.2-1.el6.noarch.rpm
rpm -i ${rpm_url}/rubygem-yajl-ruby-1.1.0-1.el6.x86_64.rpm
rpm -i ${rpm_url}/rubygem-ohai-6.14.0-1.el6.noarch.rpm
rpm -i ${rpm_url}/rubygem-netaddr-1.5.0-2.el6.noarch.rpm
rpm -i ${rpm_url}/rubygem-ipaddress-0.8.0-3.el6.noarch.rpm
rpm -i ${rpm_url}/rubygem-openstack-1.1.2-2.el6.noarch.rpm

#rubygem-netaddr-1.5.0-2.el6.noarch
#rubygem-openstack-1.1.2-2.el6.noarch





####### yum has problem ########
yum clean all
yum install -y authconfig bind-utils cronie crontabs curl gcc gdisk make mlocate nmap-ncat ntp openssh openssh-clients openssh-server perl rsync system-config-firewall-base tcpdump telnet virt-what vim wget yum yum-utils parted bfa-firmware daemonize
yum install -y nailgun-agent nailgun-mcagents nailgun-net-check puppet mcollective
#########yum end ############




########### puppet_conf ###########
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
    server = ${puppet_master}
    # How long the client should wait for the configuration to be retrieved before considering it a failure.
    # It may help with 'execution expired' issue we've experienced.
    configtimeout = 600
    # Don't send reports after every run.
    report = false

EOCONF
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
ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAuhGTD7O64zipR+XrBxgbp4pM0Ys0iFU3OuN/CPA1ViLETJljbxWe0UykE/dB5ck4EheLFNqWAkgzy4VPhLJDIp67cvM/23JpFylkiP7Ddd7Ju4hZ91sIYJqo1v70Iz+JFnntFZpej93DeBp2ACvNhizfvd4fNZvd/53k605Ms6Vr1FSmmlAARoo9v3M2FqbcnLfHsfrGHtB6m5H4LCDxSusFc2MAI9toW6LmduV8s/6fyhjF0UPR9AwaaHphcR5gFKwkjW7C91BfzfQo/gE3ykZ5TBaTFBdIni//YuCigcIKrPtA+T6GvkfzmfoHvOtFnKuAI2HVLduipIYxOWhF/Q== root@fuel.domain.tld
EOF
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


sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config

servcie iptables stop
chkconfig iptables off

#systemctl stop firewalld.service #停止firewall
#systemctl disable firewalld.service #禁止firewall开机启动

#echo "api_ip: ${master_ip}" >> /etc/nailgun-agent/config.yaml
echo "the script is completed execution........................"