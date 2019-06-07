import json
import logging
import os
import shutil
import subprocess
from time import sleep

import docker

logger = logging.getLogger().setLevel(logging.INFO)

DOCKER_PS_FORMAT = "{{.ID}};{{.Names}};{{Ports}}"
DOCKER_IMAGES_FORMAT = "{{.Repository}}:{{.Tag}}"

DOCKER_CONTAINER_NAME = "dockermon"
DOCKER_IMAGE_NAME = "dockermon:latest"

DUMP_DIR = "{}/dumps".format(os.getcwd())

TCPDUMP_INTERFACE = "eth0"
TCPDUMP_FILE_SIZE_MB = "100"
TCPDUMP_FILENAME = "eth0.cap"

TCPDUMP_CMD = "tcpdump -i {} -U -C {} -w /var/dumps/{}".format(
    TCPDUMP_INTERFACE,
    TCPDUMP_FILE_SIZE_MB,
    TCPDUMP_FILENAME
)


def has_tag(image, tag):
    for t in image.tags:
        if t == tag:
            return True
    return False


class Monitor:
    def __init__(self, client):
        self.client = client
        self.container_name = None
        self.ip_map = {}

    def monitor(self, container_name):
        client = self.client

        # Make sure any running monitor container is dead
        dockermon_containers = client.containers.list(all=True, filters={'name': DOCKER_CONTAINER_NAME})
        logging.info(dockermon_containers)
        if len(dockermon_containers) > 0:
            logging.info("Killing and removing existing dockermon container")
            dockermon_containers[0].remove(force=True)

        # Check for dockermon:latest image and built it if it doesn't exist
        images = filter(lambda i: has_tag(i, DOCKER_IMAGE_NAME), client.images.list())
        if len(images) == 0:
            logging.info("Building dockermon image (this could take a sec...)")
            client.images.build(tag="dockermon", path=".")

        # Cleanup dumps from last flter
        logging.info("Clearing dumps directory")
        if os.path.exists('./dumps'):
            shutil.rmtree(DUMP_DIR)
        os.mkdir(DUMP_DIR)

        logging.info("Starting dockermon container")
        c = client.containers.run(
            image="dockermon:latest",
            name="dockermon",
            network="container:{}".format(container_name),  # TODO - detect interface
            volumes={DUMP_DIR: {"bind": "/var/dumps", "mode": "rw"}},
            detach=True,
            command=TCPDUMP_CMD  # TODO port filters
        )

        if c:
            self.container_name = container_name

    def refresh_ip_map(self):
        p = subprocess.Popen(["docker", "network", "inspect", "bridge"], stdout=subprocess.PIPE)
        out, e = p.communicate()
        if e:
            return None

        bridge_network = json.loads(out)[0]

        ip_map = {bridge_network["IPAM"]["Config"][0]["Gateway"]: "localhost"}

        for k in iter(bridge_network["Containers"]):
            v = bridge_network["Containers"][k]
            ip_map[v["IPv4Address"][:-3]] = v["Name"]

        self.ip_map = ip_map

        return ip_map

    def get_name_from_ip(self, ip):
        return self.ip_map[ip] if ip in self.ip_map else ip

    def get_traffic(self):
        file_path = "{}/{}".format(DUMP_DIR, TCPDUMP_FILENAME)
        p = subprocess.Popen(["tcpdump", "-n", "-r", file_path], stdout=subprocess.PIPE)

        self.refresh_ip_map()

        traffic_map = {}
        seen = set()
        # TODO use awk or something fast to do the parsing
        for line in iter(p.stdout.readline, b''):
            # lil performance improvement :)
            line = " ".join(line.split(" ")[1:5])
            if line in seen:
                continue
            seen.add(line)

            parts = line.split(" ")
            if parts[0] != "IP":
                logging.warning("Skipping IPv6 stuff because it's scary")
                continue
            a, b = parts[1],    parts[3]

            part_a = a.split(".")
            host_a = self.get_name_from_ip(".".join(part_a[:4]))
            port_a = part_a[4]
            if port_a[-1] == ':':
                port_a = port_a[:-1]

            part_b = b.split(".")
            host_b = self.get_name_from_ip(".".join(part_b[:4]))
            port_b = part_b[4]
            if port_b[-1] == ':':
                port_b = port_b[:-1]

            key = " <-> ".join(sorted([host_a, host_b]))
            ports = traffic_map[key] if key in traffic_map else set()
            ports.add(port_a)
            ports.add(port_b)
            traffic_map[key] = ports

        # I AM LAZY
        for k in traffic_map:
            traffic_map[k] = list(traffic_map[k])

        return traffic_map
