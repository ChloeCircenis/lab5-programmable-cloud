#!/usr/bin/env python3

import time
import google.auth
from google.cloud import compute_v1

ZONE = "us-central1-a"
MACHINE = "e2-micro"
SNAPSHOT = "base-snapshot-lab5-flask"

_, PROJECT = google.auth.default()
instances = compute_v1.InstancesClient()

for i in range(1, 4):
    name = f"clone-{i}"

    vm = compute_v1.Instance(
        name=name,
        machine_type=f"zones/{ZONE}/machineTypes/{MACHINE}",
        disks=[
            compute_v1.AttachedDisk(
                boot=True,
                auto_delete=True,
                initialize_params=compute_v1.AttachedDiskInitializeParams(
                    source_snapshot=(
                        f"projects/{PROJECT}/global/snapshots/{SNAPSHOT}"
                    )
                )
            )
        ],
        network_interfaces=[
            compute_v1.NetworkInterface(
                network="global/networks/default"
            )
        ]
    )

    start = time.time()

    operation = instances.insert(
        project=PROJECT,
        zone=ZONE,
        instance_resource=vm
    )

    operation.result()

    elapsed = time.time() - start

    print(f"{name}: {elapsed:.2f} seconds")