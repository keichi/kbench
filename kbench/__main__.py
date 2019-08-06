import sys
import time

import click

from kubernetes import config, client
from loguru import logger

from .pod import PodLog, create_pod, wait_for_startup, delete_pod, \
                 wait_for_cleanup, print_stats
from .deployment import create_deployment, delete_deployment, \
                        rescale_deployment, wait_for_deployment_rescale


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

    for _ in range(num_pods):
        pod_name = create_pod(v1, image)
        logger.trace("Pod {} created".format(pod_name))
        pods[pod_name] = PodLog(name=pod_name, created_at=time.monotonic())

    logger.info("Waiting for pods to start")

    start = time.monotonic()

    wait_for_startup(v1, pods)

    end = time.monotonic()

    logger.info("Pod startup completed in {:.3f} [s]", end - start)

    for pod_name in pods.keys():
        delete_pod(v1, pod_name)
        logger.trace("Pod {} deleted".format(pod_name))
        pods[pod_name].deleted_at = time.monotonic()

    logger.info("Waiting for pods to exit")

    start = time.monotonic()

    wait_for_cleanup(v1, pods)

    end = time.monotonic()

    logger.info("Pod cleanup completed in {:.3f} [s]", end - start)

    print_stats(pods)


@cli.command()
@click.option("-i", "--image", default="nginx:1.17.2",
              help="Container image to use.")
@click.option("-m", "--num-replicas1", type=int, default=3,
              help="Number of replicas")
@click.option("-n", "--num-replicas2", type=int, default=5,
              help="Number of replicas")
def deployment_scaling(image, num_replicas1, num_replicas2):
    """Measure deployment scale in/out latency."""
    v1 = client.AppsV1Api()

    logger.info("Connecting to Kubernetes master at {}",
                v1.api_client.configuration.host)

    deployment_name = create_deployment(v1, image, num_replicas1)

    logger.trace("Deployment {} created".format(deployment_name))

    wait_for_deployment_rescale(v1, deployment_name, num_replicas1)

    rescale_deployment(v1, deployment_name, num_replicas2)

    wait_for_deployment_rescale(v1, deployment_name, num_replicas2)

    rescale_deployment(v1, deployment_name, num_replicas1)

    wait_for_deployment_rescale(v1, deployment_name, num_replicas1)

    delete_deployment(v1, deployment_name)

    logger.trace("Deployment {} deleted".format(deployment_name))


if __name__ == "__main__":
    cli()
