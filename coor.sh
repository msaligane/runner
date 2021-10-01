sudo -i -u runner bash
cd ~/github-actions-runner

export REPOSITORY_ORG=idea-fasoc \
    export REPOSITORY_NAME=OpenFASOC \
    export TOKEN= \
    export SLOTS=1 \
    export SCALE=1

./config.sh --url https://github.com/$REPOSITORY_ORG/$REPOSITORY_NAME \
            --token $TOKEN \
            --num $SLOTS
