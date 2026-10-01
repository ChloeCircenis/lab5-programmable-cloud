#!/usr/bin/env python3

import google.auth
from google.cloud import compute_v1

_, PROJECT = google.auth.default()

ZONE = "us-central1-a"
INSTANCE = "lab5-flask"

instances = compute_v1.InstancesClient()
disks = compute_v1.DisksClient()

instance = instances.get(
    project=PROJECT,
    zone=ZONE,
    instance=INSTANCE
)
disk_name = None
for disk in instance.disks:
    if disk.boot:
        disk_name = disk.source.split("/")[-1]
        break

snapshot = compute_v1.Snapshot(
    name=f"base-snapshot-{INSTANCE}"
)

operation = disks.create_snapshot(
    project=PROJECT,
    zone=ZONE,
    disk=disk_name,
    snapshot_resource=snapshot
)

operation.result()

print(f"Created snapshot: {snapshot.name}")