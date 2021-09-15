# GitHub Actions Runner

This repository contains the code of [GitHub Actions Runner](https://github.com/actions/runner.git) modified to spawn preemptible GCP instances with Singularity containers and to perform run steps within them.

## Description

The software was designed to run in [Google Compute Engine](https://cloud.google.com/compute).
Therefore, it is necessary to prepare some virtual infrastructure prior to installing the runner.

The repositories listed below contain the definitions of the required components:

* [github-actions-runner-scalerunner](https://github.com/antmicro/github-actions-runner-scalerunner) - the image used by preemptible GCP instances that serve as workers (one worker per job).
* [github-actions-runner-terraform](https://github.com/antmicro/github-actions-runner-terraform) - a [Terraform](https://www.terraform.io/) module used to create the virtual network, firewall rules, cloud NAT and coordinator instance for the runner.

For convenience, an [installation script](https://raw.githubusercontent.com/antmicro/runner/vm-runners/scripts/install.sh) is available that installs dependencies, configures the system, clones the repository and builds the runner.

## Installation and configuration

The manual below assumes that Debian Buster is used to deploy the runner.

### Host prerequisites

The following packages must be installed:

* `build-essential`
* [Terraform](https://www.terraform.io/docs/cli/install/apt.html)
* [Google Cloud SDK](https://cloud.google.com/sdk/docs/install#deb)

### Installation steps

With all prerequisites in place, in order to install the software, follow the steps below:

Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install#deb) and setup the project:

```bash
# Authenticate with GCP.
gcloud auth login

# Create a GCP project for your runner.
export PROJECT=example-runner-project
gcloud projects create $PROJECT
gcloud config set $PROJECT

# Create and setup a service account.
export SERVICE_ACCOUNT_ID=runner-manager
gcloud iam service-accounts create $SERVICE_ACCOUNT_ID

gcloud projects add-iam-policy-binding $PROJECT \
    --member="serviceAccount:$SERVICE_ACCOUNT_ID@$PROJECT \
    --role="roles/compute.admin"

gcloud projects add-iam-policy-binding $PROJECT \
    --member="serviceAccount:$SERVICE_ACCOUNT_ID@$PROJECT \
    --role="roles/iam.serviceAccountCreator"

gcloud projects add-iam-policy-binding $PROJECT \
    --member="serviceAccount:$SERVICE_ACCOUNT_ID@$PROJECT \
    --role="roles/iam.serviceAccountUser"

# Create and download SA key.
# WARNING: the export below will be used by Terraform later.
export GOOGLE_APPLICATION_CREDENTIALS
gcloud iam service-accounts keys create $GOOGLE_APPLICATION_CREDENTIALS \
    --iam-account=$SERVICE_ACCOUNT_ID@$PROJECT

# Create a GCP bucket for worker image.
export BUCKET=$PROJECT-worker-bucket
gsutil mb gs://$BUCKET
```

Build and upload the worker image:

```bash
# Clone the repository
git clone https://github.com/antmicro/github-actions-runner-scalerunner.git
cd github-actions-runner-scalerunner

# Compile bzImage
cd buildroot && make BR2_EXTERNAL=../overlay/ scalenode_gcp_defconfig && make

# Prepare a disk for GCP
./make_gcp_image.sh

1. Save the bucket's IAM policy to a temporary (arbitrary) JSON file
```
gsutil iam get gs://$BUCKET > /arbitrary/path/file.json
```
2. Get the project name and default service account email address. Adjust filter accordingly if a different service account is used
```
export PROJECT=$(gcloud config get-value project)
export SA=$(gcloud iam service-accounts list --filter=default | grep -E -o '[a-z0-9._%+-]+@[a-z0-9.-]+(\.[a-z0-9._%+-]+)?[a-z]{2,4}')
```
3. Get the absolute path of the Bucket config file
```
export BUCKET_FILE=/arbitrary/path/file.json
```
4. Using the `sed` utility to insert required permissions associated with the bucket
```
sed -i 's/"bindings": \[/"bindings": \[\
    {\
      "members": \[\
        "projectEditor:'"$PROJECT"'",\
        "projectOwner:'"$PROJECT"'",\
        "serviceAccount:'"$SA"'"\
      \],\
      "role": "roles\/storage.legacyBucketOwner"\
    \},/' $BUCKET_FILE
```
5. Upload the modified bucket file back to GCloud
```
gsutil iam set $BUCKET_FILE gs://$BUCKET
```
# Upload the resulting tar archive
./upload_gcp_image.sh $PROJECT $BUCKET
```

Setup virtual infrastructure using Terraform:

```bash
git clone https://github.com/antmicro/github-actions-runner-terraform.git
terraform init && terraform apply
```

Connect to the coordinator instance created in the previous step:

```bash
gcloud compute --zone <COORDINATOR_ZONE> ssh <COORDINATOR_INSTANCE>
```

Install and configure the runner on the coordinator instance:

```bash
# Download and run the installation script.
wget https://raw.githubusercontent.com/antmicro/runner/vm-runners/scripts/install.sh | bash

# The runner software runs as the 'runner' user, so let's sudo into it.
sudo -i -u runner
cd /home/runner/github-actions-runner

# Copy the .vm_specs.json file and adjust the parameters accordingly.
cp .vm_specs.example.json .vm_specs.json
vim .vm_specs.json

# Register the runner in the desired repository.
./config.sh --url https://github.com/$REPOSITORY_ORG/$REPOSITORY_NAME --token $TOKEN --num $SLOTS
```

## Starting the runner

### Manual method

In order to start the runners manually, run `SCALE=<number of slots> supervisord -n -c supervisord.conf`.

### systemd

Start the runner by running `sudo systemctl start gha-main@$SLOTS` replacing `$SLOTS` with the number of runner slots you'd like to allocate.

If you want the software to start automatically, run the command above with the `enable` action instead of `start`.
