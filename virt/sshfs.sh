#!/bin/bash

function help() {
    echo "Usage: $0 [COMMAND] [INSTANCE_NUMBER] [WORKSPACE_DIRECTORY]"
    echo ""
    echo "Where [COMMAND] is one of:"
    echo "   mount"
    echo "   umount"
    echo "   status"
    exit 1
}

cd $(dirname $0)

if [ "$#" -ne 3 ]; then
    help
fi

IP=auto-spawned$2
SHARE_PATH=$(realpath ../_layout)/_work_$2/$3
REMOTE_PATH="scalerunner@$IP:/mnt/2/work"

mkdir -p $SHARE_PATH

case "$1" in
    mount)
        echo "Mounting $REMOTE_PATH at $SHARE_PATH"
        /usr/bin/sshfs \
            -o sftp_server="/usr/bin/sudo /usr/libexec/sftp-server" \
            -o Ciphers=aes128-gcm@openssh.com \
            -o Compression=no \
            -o UserKnownHostsFile=/dev/null \
            -o StrictHostKeyChecking=no \
            -o IdentityFile=~/.ssh/id_rsa \
            -o reconnect \
            -o uid=$UID \
            -o gid=$UID \
            $REMOTE_PATH $SHARE_PATH
        exit $?
        ;;
    umount)
        echo "Unmouting $SHARE_PATH"
        fusermount -u $SHARE_PATH
        exit $?
        ;;
    status)
        mountpoint -q $SHARE_PATH
        MOUNT_STATUS=$?
        echo "$MOUNT_STATUS"
        exit $?
        ;;
    *)
        help
        ;;
esac
