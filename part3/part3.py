#!/usr/bin/env python3

import google.auth
from google.cloud import compute_v1

# ZONE = "us-central1-a"
ZONE = "us-west1-b"
VM1 = "vm1"
VM2 = "vm2"
# MACHINE = "e2-micro"
MACHINE = "f1-micro"
NETWORK = "global/networks/default"
SERVICE_ACCOUNT = (
    "lab5-vm-launcher@datacenterscalecomputinglab5.iam.gserviceaccount.com"
)

_, PROJECT = google.auth.default()
instances = compute_v1.InstancesClient()
images = compute_v1.ImagesClient()

IMAGE = images.get_from_family(
    project="ubuntu-os-cloud",
    family="ubuntu-2204-lts"
).self_link

VM2_STARTUP = """#!/bin/bash
apt-get update
apt-get install -y python3 python3-pip git
cd /opt
git clone https://github.com/cu-csci-4253-datacenter/flask-tutorial
cd flask-tutorial
python3 setup.py install
pip3 install -e .
export FLASK_APP=flaskr
flask init-db
nohup flask run -h 0.0.0.0 &
"""

VM1_STARTUP = """#!/bin/bash
apt-get update
apt-get install -y python3-pip
pip3 install google-cloud-compute
mkdir -p /srv

curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/vm2-startup \
  -o /srv/vm2-startup.sh

python3 - <<'PY'
import google.auth
from google.cloud import compute_v1

_, project = google.auth.default()
instances = compute_v1.InstancesClient()

with open("/srv/vm2-startup.sh") as f:
    startup = f.read()

vm = compute_v1.Instance(
    name="vm2",
    machine_type="zones/us-west1-b/machineTypes/f1-micro",
    disks=[
        compute_v1.AttachedDisk(
            boot=True,
            auto_delete=True,
            initialize_params=compute_v1.AttachedDiskInitializeParams(
                source_image="__IMAGE__"
            )
        )
    ],
    network_interfaces=[
        compute_v1.NetworkInterface(
            network="global/networks/default",
            access_configs=[
                compute_v1.AccessConfig(
                    name="External NAT",
                    type_="ONE_TO_ONE_NAT"
                )
            ]
        )
    ],
    tags=compute_v1.Tags(items=["allow-5000"]),
    metadata=compute_v1.Metadata(items=[
        compute_v1.Items(
            key="startup-script",
            value=startup
        )
    ])
)

instances.insert(
    project=project,
    zone="us-west1-b",
    instance_resource=vm
).result()

print("VM-2 created")
PY
"""

VM1_STARTUP = VM1_STARTUP.replace("__IMAGE__", IMAGE)

vm1 = compute_v1.Instance(
    name=VM1,
    machine_type=f"zones/{ZONE}/machineTypes/{MACHINE}",
    disks=[
        compute_v1.AttachedDisk(
            boot=True,
            auto_delete=True,
            initialize_params=compute_v1.AttachedDiskInitializeParams(
                source_image=IMAGE
            )
        )
    ],
    network_interfaces=[
        compute_v1.NetworkInterface(
            network=NETWORK,
            access_configs=[
                compute_v1.AccessConfig(
                    name="External NAT",
                    type_="ONE_TO_ONE_NAT"
                )
            ]
        )
    ],
    service_accounts=[
        compute_v1.ServiceAccount(
            email=SERVICE_ACCOUNT,
            scopes=[
                "https://www.googleapis.com/auth/cloud-platform"
            ]
        )
    ],
    metadata=compute_v1.Metadata(items=[
        compute_v1.Items(
            key="startup-script",
            value=VM1_STARTUP
        ),
        compute_v1.Items(
            key="vm2-startup",
            value=VM2_STARTUP
        )
    ])
)

print("Creating VM-1...")

instances.insert(
    project=PROJECT,
    zone=ZONE,
    instance_resource=vm1
).result()

print("VM-1 created")