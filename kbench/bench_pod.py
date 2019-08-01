#!/usr/bin/env python3

import statistics
import time

import click

from kubernetes import client, config
from kubernetes.watch import Watch
from loguru import logger

POD_PREFIX = "kbench-"
CONTAINER_NAME = "kbench-container"
NAMESPACE = "default"


class PodLog:
    def __init__(self, name=None, created_at=None, started_at=None,
                 deleted_at=None, exited_at=None):
        self.name = name
        self.created_at = created_at
        self.started_at = started_at
        self.deleted_at = deleted_at
        self.exited_at = exited_at


def create_pod(v1, image):
    container = client.V1Container(name=CONTAINER_NAME, image=image)
    spec = client.V1PodSpec(containers=[container])
    meta = client.V1ObjectMeta(generate_name=POD_PREFIX)
    pod = client.V1Pod(spec=spec, metadata=meta)

    ret = v1.create_namespaced_pod(NAMESPACE, pod)

    return ret.metadata.name


def wait_for_startup(v1, pods):
    pending = set(pods.keys())
    watch = Watch()

    for event in watch.stream(v1.list_namespaced_pod, namespace=NAMESPACE):
        pod = event["object"]
        name = pod.metadata.name

        if name in pending and pod.status.phase == "Running":
            pods[name].started_at = time.monotonic()
            logger.trace("Pod {} started in {:.3f} [s]", name,
                         pods[name].started_at - pods[name].created_at)

            pending.remove(name)

            if not pending:
                return


def delete_pod(v1, name):
    # delete_collection_namespaced_pod is maybe better?
    v1.delete_namespaced_pod(name=name, namespace=NAMESPACE)


def wait_for_cleanup(v1, pods):
    pending = set(pods)
    watch = Watch()

    for event in watch.stream(v1.list_namespaced_pod, namespace=NAMESPACE):
        type = event["type"]
        pod = event["object"]
        name = pod.metadata.name

        if name in pending and type == "DELETED":
            pods[name].exited_at = time.monotonic()
            logger.trace("Pod {} exited in {:.3f} [s]", name,
                         pods[name].exited_at - pods[name].deleted_at)

            pending.remove(name)

            if not pending:
                return


def startup_pods(num_pods, image, v1, pods):
    for _ in range(num_pods):
        pod_name = create_pod(v1, image)
        logger.trace("Pod {} created".format(pod_name))
        pods[pod_name] = PodLog(name=pod_name, created_at=time.monotonic())

    logger.info("Waiting for pods to start")

    start = time.monotonic()

    wait_for_startup(v1, pods)

    end = time.monotonic()

    logger.info("Pod startup completed in {:.3f} [s]", end - start)


def cleanup_pods(num_pods, image, v1, pods):
    for pod_name in pods.keys():
        delete_pod(v1, pod_name)
        logger.trace("Pod {} deleted".format(pod_name))
        pods[pod_name].deleted_at = time.monotonic()

    logger.info("Waiting for pods to exit")

    start = time.monotonic()

    wait_for_cleanup(v1, pods)

    end = time.monotonic()

    logger.info("Pod cleanup completed in {:.3f} [s]", end - start)


@click.command()
@click.option("-n", "--num-pods", default=5, type=int,
              help="number of pods to launch")
@click.option("-i", "--image", default="nginx:1.17.2",
              help="container image to use")
def cli(num_pods, image):
    logger.info("Will launch {} pods with image {}", num_pods, image)

    config.load_kube_config()

    v1 = client.CoreV1Api()

    logger.info("Connecting to Kubernetes master at {}",
                v1.api_client.configuration.host)

    pods = {}

    startup_pods(num_pods, image, v1, pods)
    cleanup_pods(num_pods, image, v1, pods)

    startup = [log.started_at - log.created_at for log in pods.values()]
    logger.info("Pod startup: min={:.3f} [s], avg={:.3f} [s], max={:.3f} [s]",
                min(startup), statistics.mean(startup), max(startup))

    cleanup = [log.exited_at - log.deleted_at for log in pods.values()]
    logger.info("Pod cleanup: min={:.3f} [s], avg={:.3f} [s], max={:.3f} [s]",
                min(cleanup), statistics.mean(cleanup), max(cleanup))


if __name__ == "__main__":
    cli()
