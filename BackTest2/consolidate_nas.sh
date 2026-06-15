#!/bin/bash
set -e

echo "Stopping containers..."
sudo docker stop windrose portainer || true

echo "Stopping services..."
sudo systemctl stop docker
sudo systemctl stop smb nmb || sudo systemctl stop samba

echo "Creating new docker root on NAS..."
sudo mkdir -p /mnt/nas/docker

echo "Migrating docker data from /mnt/docker to /mnt/nas/docker..."
# -a preserves permissions, -v for verbose, -P for progress
sudo rsync -avP /mnt/docker/ /mnt/nas/docker/

echo "Deleting CoreKeeper data as requested..."
sudo rm -rf /mnt/nas/docker/volumes/corekeeper_server
sudo rm -rf /mnt/nas/docker/volumes/corekeeper_saves

echo "Updating Docker configuration..."
if [ ! -d /etc/docker ]; then
    sudo mkdir -p /etc/docker
fi
echo '{"data-root": "/mnt/nas/docker"}' | sudo tee /etc/docker/daemon.json

echo "Updating Samba configuration..."
# Backup existing config
sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.bak

# Create new simplified config
# We will keep the global section and only the [NAS] share
sudo sed -i '/^\[Docker\]/,$d' /etc/samba/smb.conf

# Re-append only the NAS share if it was deleted or just to be safe
# (Actually, let's just write a clean version of shares)
# Based on previous 'cat' output, [NAS] was the first share.

echo "Samba config updated. Restarting services..."
sudo systemctl start docker
sudo systemctl start smb nmb || sudo systemctl start samba

echo "Cleaning up..."
# Optionally unmount /mnt/docker or leave it for now.
# User didn't ask to remove the disk, just the network drives.

echo "Consolidation complete."
