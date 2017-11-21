ifconfig eth1 10.20.0.8 netmask 255.255.255.0

mkdir -p /root/.ssh
chmod 700 /root/.ssh

######publickey depend fuel master#######
cat > /root/.ssh/authorized_keys <<EOF
ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAyFkNGtr5g4AirTIwWhTzrFm0RycXlFxK3T/c5MIQ5/QlZaM9FjHp7ozQRULwszZoF+Dn1SusC2nhn+yRTvB6dBNqobcNJctBlaEhkMsr941lGDkE9W8daP6mREoSLASYTINkfD3uUbT+V3P7YEDPFv6BxzTyh7tBBu1V2A0cutPeaMJcHqUTL+JeDz/XRcFKn+dkxL0NF/fWiBEgMAmiHIRxcFknws3r8BL/nLgWWU4Zgf0K1dXT3Y/sZHXmh16PiiAIWHtlfwnC+/TtLX4nj8aSEE+laxtXnykLlLT+KYYwsOBP8jJwW7AZ3YaUn+dmQ2xN5TBgaY5TKPgHts4otw== root@fuel.domain.tld
EOF

chmod 600 /root/.ssh/authorized_keys


#######sshd_config############
sed -i 's/^#RSAAuthentication/RSAAuthentication/' /etc/ssh/sshd_config
sed -i 's/^#PubkeyAuthentication/PubkeyAuthentication/' /etc/ssh/sshd_config
sed -i 's/^#AuthorizedKeysFile/AuthorizedKeysFile/' /etc/ssh/sshd_config

service sshd restart

