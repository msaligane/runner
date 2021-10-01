# Setup prerequisites
sudo apt install build-essential -y
sudo apt install git wget unzip rsync bc \
    libelf-dev autotools-dev automake \
    gcc-multilib texinfo dosfstools mtools -y

# Install Go for compiling BzImage
cd ~
wget https://golang.org/dl/go1.16.5.linux-amd64.tar.gz && \
    sudo tar -xzf go1.16.5.linux-amd64.tar.gz -C /usr/local/ && \
    export PATH=$PATH:/usr/local/go/bin

# Install Terraform
sudo apt-get install software-properties-common -y
curl -fsSL https://apt.releases.hashicorp.com/gpg | 
    sudo apt-key add -
sudo apt-add-repository "deb [arch=$(dpkg --print-architecture)] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt update && sudo apt install terraform -y

# Install Google Cloud SDK
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | 
    sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

sudo apt-get install apt-transport-https ca-certificates gnupg -y
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | 
    sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -

sudo apt-get update && sudo apt-get install google-cloud-sdk -y

# Rebuild image
git clone --recursive \
    https://github.com/antmicro/github-actions-runner-scalerunner.git && \
        cd github-actions-runner-scalerunner/buildroot && \
        make BR2_EXTERNAL=../overlay/ scalenode_gcp_defconfig && \
        make

export PROJECT=catx-ext-umich && \
    export BUCKET=$PROJECT-worker-bucket

# Make and upload image
cd ../ && \
    ./make_gcp_image.sh && \
    ./upload_gcp_image.sh $PROJECT $BUCKET


export name=$(gcloud compute instances list | grep gha | awk '{print $1}') && \
    export zone=$(gcloud compute instances list | grep gha | awk '{print $2}') && \
    cat coor.sh | gcloud compute ssh $name --zone=$zone

