#!/bin/bash

set -e

cd $(dirname $0)

while getopts ":n:r:s:" o; do
    case "${o}" in
        n)
            PREFIX=${OPTARG}
            ;;
        s)
            CONTAINER=${OPTARG}
            ;;
        *)
            echo "Provide all arguments!"
            exit 1
            ;;
    esac
done
shift $((OPTIND-1))

WORKDIR=$(realpath work)
OVERLAY_IMG=$WORKDIR/${PREFIX}_overlay.img
SIF_FILE=$WORKDIR/sif/$CONTAINER.sif
FREE_SPACE=$(df -B1 . | tail -n +2 | awk '{ print $4 "\t" }')
OVERLAY_SIZE=70G
DUMMY_DISK=$WORKDIR/small.img
SSH_PUB_KEY=$HOME/.ssh/id_rsa

TAP=tap${PREFIX}

Q=$WORKDIR/${PREFIX}_qemu
Q2=$WORKDIR/${PREFIX}_qemu_mon
SIN=$Q.in
SOUT=$Q.out
MIN=$Q2.in
MOUT=$Q2.out

echo "Instance number:  ${PREFIX}"
echo "Share path:       ${SHARE_PATH}"

readUntilString() {
	echo "Reading serial until: $1"
	while read line; do
		echo "${line}"
		if [[ ${line} == *"$1"* ]]; then
			echo "Not reading serial anymore."
			break;
		fi
	done < $SOUT
}

writeSer() {
	echo $1 > $SIN
	sleep 0.2
}

sshSend() {
    echo $@
    /usr/bin/ssh -q \
        -o "UserKnownHostsFile /dev/null" \
        -o "StrictHostKeyChecking no" \
        scalerunner@172.17.$PREFIX.2 << EOF
sudo -s
$@
EOF
}

if [ -f "$OVERLAY_IMG" ]; then
	rm -rf $OVERLAY_IMG
fi

if [ ! -f "$SSH_PUB_KEY" ]; then
	ssh-keygen -t rsa -f $SSH_PUB_KEY -q -P ""
fi

if [ ! -f "$DUMMY_DISK" ]; then
	fallocate -l 1MB $DUMMY_DISK
fi

fallocate -l $OVERLAY_SIZE $OVERLAY_IMG

mkfifo $SIN $SOUT $MIN $MOUT || true

qemu-system-x86_64 \
	-kernel $WORKDIR/bzImage-2021-01-04--12-34-20 \
	-m 20G -append "console=ttyS0" -enable-kvm -smp 4 -cpu host \
	-drive format=raw,file.filename=$SIF_FILE,file.locking=off,file.driver=file,snapshot=on \
	-drive format=raw,file.filename=$DUMMY_DISK,file.locking=off,file.driver=file,snapshot=on \
	-drive format=raw,file.filename=$DUMMY_DISK,file.locking=off,file.driver=file,snapshot=on \
	-drive format=raw,file=$OVERLAY_IMG \
	-nic tap,ifname=$TAP,script=no,downscript=no,model=virtio-net-pci \
	-smbios type=1,manufacturer=Antmicro,product="Antmicro Compute Engine",version="" \
	-smbios type=2,manufacturer=Antmicro,product="Antmicro Compute Engine",version="" \
	-smbios type=11,value="set_hostname scalenode-github" \
	-smbios type=11,value="inject_key scalerunner:'$(cat ${SSH_PUB_KEY}.pub)'" \
	-serial pipe:$Q \
	-monitor pipe:$Q2 \
	-pidfile $Q.pid \
	-display none \
	-daemonize \
	--enable-kvm


readUntilString "Welcome to Buildroot"

sshSend "mke2fs /dev/sdd"
sshSend "mount /dev/sdd /mnt"
sshSend "mkdir -p /mnt/1 /mnt/2/work"
sshSend "singularity instance start -C -e --dns 8.8.8.8 --overlay /mnt/1 --bind /mnt/2:/root /tmp/container.sif i"
