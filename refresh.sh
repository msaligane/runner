# Stop instance before deleting
gcloud compute instances stop instance-2

# Delete then create instance
gcloud compute instances delete instance-2

gcloud compute instances create instance-2 --project=catx-ext-umich \
--zone=us-central1-a \
--machine-type=e2-standard-32 \
--network-interface=network-tier=PREMIUM,subnet=default \
--maintenance-policy=MIGRATE \
--service-account=terraform-runner@catx-ext-umich.iam.gserviceaccount.com \
--scopes=https://www.googleapis.com/auth/cloud-platform \
--create-disk=auto-delete=yes,boot=yes,device-name=instance-2, \
image=projects/debian-cloud/global/images/debian-10-buster-v20210916, \
mode=rw,size=256, \
type=projects/catx-ext-umich/zones/us-central1-a/diskTypes/pd-balanced \
--no-shielded-secure-boot --shielded-vtpm \
--shielded-integrity-monitoring --reservation-affinity=any
