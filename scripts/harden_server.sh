#!/bin/bash
# harden_server.sh
# Applies server hardening measures: UFW, SSH hardening, Fail2Ban, and Unattended Upgrades.

set -e

echo "=== Starting Server Hardening ==="

# 1. Update and install necessary packages
echo ">>> Installing Fail2Ban and Unattended-Upgrades..."
sudo apt-get update
sudo apt-get install -y fail2ban ufw unattended-upgrades

# 2. UFW Configuration
echo ">>> Configuring UFW..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
echo "y" | sudo ufw enable

# 3. SSH Hardening
echo ">>> Hardening SSH..."
sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#*X11Forwarding.*/X11Forwarding no/' /etc/ssh/sshd_config
sudo sed -i 's/^#*MaxAuthTries.*/MaxAuthTries 3/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# 4. Fail2Ban Configuration
echo ">>> Configuring Fail2Ban..."
cat <<EOF | sudo tee /etc/fail2ban/jail.local
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF

sudo systemctl enable fail2ban
sudo systemctl restart fail2ban

# 5. Unattended Upgrades
echo ">>> Configuring Unattended Upgrades..."
sudo dpkg-reconfigure -f noninteractive unattended-upgrades

echo "=== Server Hardening Complete ==="
echo "Note: Ensure your SSH keys are configured correctly before logging out!"
