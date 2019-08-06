import sys
import time

from contextlib import contextmanager

import click

from kubernetes import config, client
from loguru import logger

from .pod import PodLog, create_pod, wait_for_startup, delete_pod, \
                 wait_for_cleanup, print_stats
from .deployment import create_deployment, delete_deployment, \
                        rescale_deployment, wait_for_deployment_rescale


@contextmanager
def timer(name):
    start = time.monotonic()
    yield
    end = time.monotonic()

    logger.info("{} completed in {:.3f} [s]", name, end - start)


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging.")
def cli(verbose):
    config.load_kube_config()

    log_level = "INFO"
    if verbose:
        log_level = "TRACE"

    handler = {
        "sink": sys.stderr,
        "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
                  "<level>{level}</level> {message}",
        "level": log_level
    }
    logger.configure(handlers=[handler])


@cli.command()
@click.option("-n", "--num-pods", default=5, type=int,
              help="Number of pods to launch.")
@click.option("-i", "--image", default="nginx:1.17.2",
              help="Container image to use.")
def pod_latency(num_pods, image):
    """Measure pod startup/cleanup latency."""
    logger.info("Will launch {} pods with image {}", num_pods, image)

    v1 = client.CoreV1Api()

    logger.info("Connecting to Kubernetes master at {}",
                v1.api_client.configuration.host)

    pods = {}

    for _ in range(num_pods):
        pod_name = create_pod(v1, image)
        pod_log = PodLog(name=pod_name, created_at=time.monotonic())

        tmp = {pod_name: pod_log}

        wait_for_startup(v1, tmp)

        delete_pod(v1, pod_name)
        pod_log.deleted_at = time.monotonic()

        wait_for_cleanup(v1, tmp)

        pods[pod_name] = pod_log

    print_stats(pods)


@cli.command()
@click.option("-n", "--num-pods", default=5, type=int,
              help="Number of pods to launch.")
@click.option("-i", "--image", default="nginx:1.17.2",
              help="Container image to use.")
def pod_throughput(num_pods, image):
    """Measure pod startup/cleanup throughput."""
    logger.info("Will launch {} pods with image {}", num_pods, image)

    v1 = client.CoreV1Api()

    logger.info("Connecting to Kubernetes master at {}",
                v1.api_client.configuration.host)

    pods = {}

    with timer("Pod startup"):
        for _ in range(num_pods):
            pod_name = create_pod(v1, image)
            logger.trace("Pod {} created", pod_name)
            pods[pod_name] = PodLog(name=pod_name, created_at=time.monotonic())

        logger.info("Waiting for pods to start")

        wait_for_startup(v1, pods)

    with timer("Pod cleanup"):
        for pod_name in pods.keys():
            delete_pod(v1, pod_name)
            logger.trace("Pod {} deleted", pod_name)
            pods[pod_name].deleted_at = time.monotonic()

        logger.info("Waiting for pods to exit")

        wait_for_cleanup(v1, pods)

    print_stats(pods)


@cli.command()
@click.option("-i", "--image", default="nginx:1.17.2",
              help="Container image to use.")
@click.option("-m", "--num-init-replicas", type=int, default=3,
              help="Initial number of replicas")
@click.option("-n", "--num-target-replicas", type=int, default=5,
              help="Target number of replicas.")
def deployment_scaling(image, num_init_replicas, num_target_replicas):
    """Measure deployment scale-in/out latency."""
    v1 = client.AppsV1Api()

    logger.info("Connecting to Kubernetes master at {}",
                v1.api_client.configuration.host)

    with timer("Deployment creation"):
        deployment_name = create_deployment(v1, image, num_init_replicas)
        wait_for_deployment_rescale(v1, deployment_name, num_init_replicas)
        logger.info("Deployment {} created with {} replicas", deployment_name,
                    num_init_replicas)

    with timer("Deployment scale-out"):
        rescale_deployment(v1, deployment_name, num_target_replicas)
        wait_for_deployment_rescale(v1, deployment_name, num_target_replicas)
        logger.trace("Deployment {} scaled to {} replicas", deployment_name,
                     num_target_replicas)

    with timer("Deployment scale-in"):
        rescale_deployment(v1, deployment_name, num_init_replicas)
        wait_for_deployment_rescale(v1, deployment_name, num_init_replicas)
        logger.trace("Deployment {} scaled to {} replicas", deployment_name,
                     num_init_replicas)

    delete_deployment(v1, deployment_name)


if __name__ == "__main__":
    cli()
