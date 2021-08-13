#!/bin/bash

set -e

cd $(dirname $0)

PREFIX=$1
IP_PREFIX=`hostname`
SSH_HOST=$IP_PREFIX-auto-spawned$PREFIX

sshSend() {
    echo "# connecting to $SSH_HOST"
    echo "+ $@"
    /usr/bin/ssh -q \
        -o "UserKnownHostsFile /dev/null" \
        -o "StrictHostKeyChecking no" \
        -o "ServerAliveInterval 10" \
        -o "ConnectTimeout 10" \
        -o "ConnectionAttempts 3" \
        scalerunner@$SSH_HOST << EOF
sudo -s
$@
EOF
}

echo "# `getent hosts $SSH_HOST`"
sshSend "mkdir -p /root/work"
sshSend "mount --bind /mnt/2/work /root/work"
sshSend 'cd /root/work;for f in $(find -type l);do cp -f $(readlink $f) $f || true;done;'
sshSend 'cd /root/work;find -type l -exec unlink {} \;'
sshSend "umount /root/work"
