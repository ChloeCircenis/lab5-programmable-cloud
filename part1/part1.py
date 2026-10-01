#!/usr/bin/env python3

import google.auth
from google.api_core.exceptions import NotFound
from google.cloud import compute_v1

# ZONE = "us-west1-b"
ZONE = "us-central1-a"
NAME = "lab5-flask"
# MACHINE = "f1-micro"
MACHINE = "e2-micro"
NETWORK = "global/networks/default"
TAG = "allow-5000"

_, PROJECT = google.auth.default()
instances = compute_v1.InstancesClient()
firewalls = compute_v1.FirewallsClient()
images = compute_v1.ImagesClient()

image = images.get_from_family(
    project="ubuntu-os-cloud",
    family="ubuntu-2204-lts"
).self_link

def wait(op):
    op.result()


startup = """#!/bin/bash
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

vm = compute_v1.Instance(
    name=NAME,
    machine_type=f"zones/{ZONE}/machineTypes/{MACHINE}",
    disks=[compute_v1.AttachedDisk(
        boot=True,
        auto_delete=True,
        initialize_params=compute_v1.AttachedDiskInitializeParams(
            source_image=image
        )
    )],
    network_interfaces=[compute_v1.NetworkInterface(
        network=NETWORK,
        access_configs=[compute_v1.AccessConfig(
            name="External NAT",
            type_="ONE_TO_ONE_NAT"
        )]
    )],
    metadata=compute_v1.Metadata(items=[
        compute_v1.Items(key="startup-script", value=startup)
    ])
)

wait(instances.insert(
    project=PROJECT,
    zone=ZONE,
    instance_resource=vm
))

try:
    firewalls.get(project=PROJECT, firewall=TAG)
except NotFound:
    wait(firewalls.insert(
        project=PROJECT,
        firewall_resource=compute_v1.Firewall(
            name=TAG,
            network=NETWORK,
            direction="INGRESS",
            source_ranges=["0.0.0.0/0"],
            target_tags=[TAG],
            allowed=[compute_v1.Allowed(
                I_p_protocol="tcp",
                ports=["5000"]
            )]
        )
    ))

vm = instances.get(project=PROJECT, zone=ZONE, instance=NAME)
wait(instances.set_tags(
    project=PROJECT,
    zone=ZONE,
    instance=NAME,
    tags_resource=compute_v1.Tags(
        items=[TAG],
        fingerprint=vm.tags.fingerprint
    )
))

vm = instances.get(project=PROJECT, zone=ZONE, instance=NAME)
ip = vm.network_interfaces[0].access_configs[0].nat_i_p

print(f"http://{ip}:5000")