# GitHub Actions Runner

This repository contains the code of [GitHub Actions Runner](https://github.com/actions/runner.git) modified to spawn preemptible GCP instances with Singularity containers and to perform run steps within them.

## Description

The software was designed to run in [Google Compute Engine](https://cloud.google.com/compute).
Therefore, it is necessary to prepare some virtual infrastructure prior to installing the runner.

The repositories enlisted below contain the definitions of the required components:

* [github-actions-runner-scalerunner](https://github.com/antmicro/github-actions-runner-scalerunner) - the image used by preemptible GCP instances that serve as workers (one worker per job).
* [github-actions-runner-terraform](https://github.com/antmicro/github-actions-runner-terraform) - a [Terraform](https://www.terraform.io/) module used to create virtual network, firewall rules, cloud NAT and coordinator instance for the runner.

For added convenience, an [installation script](https://raw.githubusercontent.com/antmicro/runner/vm-runners/scripts/install.sh) is available that installs dependencies, configures the system, clones the repository and builds the runner.

# Installation and configuration

In order to install the software, follow the steps below.

1. Create a GCP project for your runner, create a service account with scopes described in [Terraform module README](https://raw.githubusercontent.com/antmicro/github-actions-runner-terraform/main/README.md).
1. Clone the [github-actions-runner-scalerunner](https://github.com/antmicro/github-actions-runner-scalerunner), build the image and upload it using the `upload_gcp_image.sh` script.
1. Generate and download a key file for the SA and set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of the service account key.
1. Install [Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli).
1. Clone the [github-actions-runner-terraform](https://github.com/antmicro/github-actions-runner-terraform) repository.
1. Enter the freshly cloned repository and run `terraform init && terraform apply`.
1. An interactive prompt will ask you for the infrastructure settings.
1. Once the infrastructure has been provisioned, SSH into the newly created coordinator instance.
1. Fetch the [installation script](https://raw.githubusercontent.com/antmicro/runner/vm-runners/scripts/install.sh) and run it.
1. Change working directory into the runner repository.
1. Copy the `.vm_specs.example.json` to `.vm_specs.json` and adjust the parameters accordingly.
1. Registering the runner in a repository by running `./config.sh --url https://github.com/$REPOSITORY_ORG/$REPOSITORY_NAME --token $TOKEN --num $SLOTS` with `$TOKEN` being the registration token found in the **Actions** tab in the repository settings and `$SLOTS` being the number of runner slots to allocate.
1. Start the runner using either method described below.

## Starting the runner

### Manual method

In order to start runners, run `SCALE=<number of slots> supervisord -n -c supervisord.conf`.

### systemd

Start the runner by running `sudo systemctl start gha-main@$SLOTS` replacing `$SLOTS` with the number of runner slots you'd like to allocate.

If you want the software to start automatically, run the command above with the `enable` verb instead of `start`.
