# GitHub Actions Runner

This repository contains the code of [GitHub Actions Runner](https://github.com/actions/runner.git) modified to spawn preemptible GCP instances with Singularity containers and to perform run steps within them.

## Installation

This software has been tested to work on Debian Buster and Bullseye.

It is recommended to perform the installation of this software on a fresh, dedicated machine.

For added convenience, an [installation script](https://raw.githubusercontent.com/antmicro/runner/vm-runners/scripts/install.sh) is available that installs dependencies, configures the system, clones the repository and builds the runner.

The next step is defining the parameters of GCP instances which will be spawned.
Simply copy the `.vm_specs.example.json` to `.vm_specs.json` and adjust the parameters accordingly.

The last step is registering the runner in a repository.
To do this, run `./config.sh --url https://github.com/$REPOSITORY_ORG/$REPOSITORY_NAME --token $TOKEN --num $SLOTS` with `$TOKEN` being the registration token found in the **Actions** tab in the repository settings and `$SLOTS` being the number of runner slots to allocate.

## Starting the runner

### Manual method

In order to start runners, run `SCALE=<number of slots> supervisord -n -c supervisord.conf`.

### systemd

Start the runner by running `sudo systemctl start gha-main@$SLOTS` replacing `$SLOTS` with the number of runner slots you'd like to allocate.
