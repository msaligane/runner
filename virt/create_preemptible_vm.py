#!/usr/bin/python3
import subprocess, json, click, paramiko
from collections import namedtuple

def load_config():
    with open('../.vm_specs.json', 'r') as f:
        return json.load(f, object_hook=lambda d: namedtuple('vm_specs', d.keys())(*d.values()))

@click.command()
@click.option('-n', '--instance-number', help='Instance number', required=True)
@click.option('-s', '--container-file', help='Container file', required=True)
def main(instance_number, container_file):
    c = load_config()

    machine_type = c.gcp.type
    overlay_size_gb = c.machine.disk

    project_id = c.gcp.project
    zone = c.gcp.zone
    instance_name = f'auto-spawned{instance_number}'

    print(f'{instance_name=}')
    print(f'{container_file=}')
    subnet = 'runner-test'

    key = (open('/home/runner/.ssh/id_rsa.pub')
          .read()
          .strip()
	  .translate(str.maketrans({'+': r'\+', ' ': r'\ '}))	
    )
    try:
        output = subprocess.check_output(
                f'gcloud beta compute --project={project_id} '
                f'instances create {instance_name} --zone={zone} '
                f'--machine-type={machine_type} --subnet={subnet} '
                '--no-address --network-tier=PREMIUM '
                '--metadata=serial-port-enable=true,'
                'ssh-keys=coordinator:'
                f'{key} '
                '--no-restart-on-failure --tags=runners '
                '--maintenance-policy=TERMINATE --preemptible '
                '--service-account=238820661769-compute'
                '@developer.gserviceaccount.com '
                '--scopes=https://www.googleapis.com/auth/devstorage.read_only,'
                'https://www.googleapis.com/auth/logging.write,'
                'https://www.googleapis.com/auth/monitoring.write,'
                'https://www.googleapis.com/auth/servicecontrol,'
                'https://www.googleapis.com/auth/service.management.readonly,'
                'https://www.googleapis.com/auth/trace.append '
                f'--image={c.gcp.image} --image-project={c.gcp.project} '
                f'--boot-disk-size={overlay_size_gb}GB '
                '--boot-disk-type=pd-balanced '
                f'--boot-disk-device-name={instance_name} '
                '--reservation-affinity=any',
                shell=True
        ).decode("utf-8")

        print(output)

    except subprocess.CalledProcessError as err:
        # failed to spawn the machine
        print(err)
        exit()

    except OSError:
        print('unable to write to log file')
    
    info = ' '.join(output.split('\n')[1].split())
    # gcloud prints these to stdout in [1] line, separated with spaces
    name, zone, mach_type, preemptible, internal_ip, status = info.split(' ')

    # this is the name recognized by DNS in Google
    target = f'{name}.{zone}.c.{project_id}.internal'

    # scp public key to authorized_keys of the minion machine
    try:
        result = subprocess.check_output(
                'sshpass -p scalerunner scp -q '
                '-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no '
                f'~/.ssh/id_rsa.pub scalerunner@{target}:~/.ssh/authorized_keys ',
                shell=True
        )
    except subprocess.CalledProcessError as err:
        print('Failed to copy public ssh key to authorized_keys of the runner:')
        print(err)

    ssh = paramiko.SSHClient()
    ssh.get_host_keys()
    ssh.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
    ssh.connect(target, username='scalerunner')

    commands = (
        'uname -a',
        'sudo mkdir -p /mnt/1 /mnt/2/work /mnt/3',
	f'sudo singularity pull /mnt/container.sif docker://{container_file}',
        'sudo singularity instance start -C -e --dns 8.8.8.8 --overlay /mnt/1 --bind /mnt/2:/root /mnt/container.sif i',
        #'SARGRAPH_OUTPUT_TYPE=svg sargraph chart start',
    )

    for cmd in commands:
        _, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.readlines())
        print(stderr.readlines())

if __name__ == '__main__':
    main()
