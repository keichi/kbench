from kubernetes import client
from kubernetes.watch import Watch
from loguru import logger

from .consts import CONTAINER_NAME, DEPLOYMENT_PREFIX, NAMESPACE


def create_deployment(v1, image, num_replicas):
    container = client.V1Container(name=CONTAINER_NAME, image=image)
    container_spec = client.V1PodSpec(containers=[container])
    meta = client.V1ObjectMeta(labels=dict(app="kbench"))
    template_spec = client.V1PodTemplateSpec(spec=container_spec,
                                             metadata=meta)
    selector = client.V1LabelSelector(match_labels=dict(app="kbench"))
    deployment_spec = client.V1DeploymentSpec(template=template_spec,
                                              replicas=num_replicas,
                                              selector=selector)
    meta = client.V1ObjectMeta(generate_name=DEPLOYMENT_PREFIX)
    deployment_spec = client.V1Deployment(spec=deployment_spec, metadata=meta)

    deployment = v1.create_namespaced_deployment(body=deployment_spec,
                                                 namespace=NAMESPACE)

    return deployment.metadata.name


def delete_deployment(v1, name):
    v1.delete_namespaced_deployment(name=name, namespace=NAMESPACE)


def wait_for_deployment_rescale(v1, name, target_replicas):
    watch = Watch()
    for event in watch.stream(v1.list_namespaced_deployment,
                              namespace=NAMESPACE):
        deployment = event["object"]

        if deployment.metadata.name != name:
            continue

        ready_replicas = deployment.status.ready_replicas

        if ready_replicas is None:
            ready_replicas = 0

        logger.trace("Deployment {} has {} replicas", name, ready_replicas)

        if ready_replicas == target_replicas:
            return


def rescale_deployment(v1, name, num_replicas):
    logger.info("Rescaling deployment {} to {} replicas", name, num_replicas)

    scale = client.V1Scale(spec=client.V1ScaleSpec(replicas=num_replicas))
    v1.patch_namespaced_deployment_scale(name=name, namespace=NAMESPACE,
                                         body=scale)
