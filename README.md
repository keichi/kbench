# kbench
[![CircleCI](https://circleci.com/gh/keichi/kbench.svg?style=svg)](https://circleci.com/gh/keichi/kbench)
[![PyPI](https://img.shields.io/pypi/v/kbench?style=flat-square)](https://pypi.org/project/kbench)

kbench is a benchmarking tool for measuring the control plane performance of a
Kubernetes cluster.

## Installation

kbench is available on PyPI.

```
$ pip3 install kbench
```

## Usage

### pod-throughput

Launch multiple pods in parallel and measure their startup and cleanup time.

```
$ kbench pod-throughput
```

- `-n`, `--num-pods`: Number of pods to launch.
- `-i`, `--image`: Container image to use.
- `--timings` / `--no-timings`:  Print timing information for all pods.

### pod-latency

Launch multiple pods sequentially and measure their startup and cleanup time.

```
$ kbench pod-latency
```

- `-n`, `--num-pods`: Number of pods to launch.
- `-i`, `--image`: Container image to use.
- `--timings` / `--no-timings`:  Print timing information for all pods.

### deployment-scaling

Create a deployment and measure scale-in/out latency. First, a deployment with
`m` replicas is created. Then, the deployment is scaled-out to `n` replicas.
Once the scale-out is completed, the deployment is scaled-in to `m` replicas
again.

```
$ kbench deployment-scaling
```

- `-i`, `--image`: Container image to use.
- `-m`, `--num-init-replicas`: Initial number of replicas.
- `-n`, `--num-target-replicas`: Target number of replicas.
