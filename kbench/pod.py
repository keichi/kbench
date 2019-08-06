import statistics
import time

from kubernetes import client
from kubernetes.watch import Watch
from loguru import logger

from .consts import POD_PREFIX, CONTAINER_NAME, NAMESPACE


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


def print_stats(pods):
    startup = [log.started_at - log.created_at for log in pods.values()]
    logger.info("Pod startup: min={:.3f} [s], avg={:.3f} [s], max={:.3f} [s]",
                min(startup), statistics.mean(startup), max(startup))

    cleanup = [log.exited_at - log.deleted_at for log in pods.values()]
    logger.info("Pod cleanup: min={:.3f} [s], avg={:.3f} [s], max={:.3f} [s]",
                min(cleanup), statistics.mean(cleanup), max(cleanup))
