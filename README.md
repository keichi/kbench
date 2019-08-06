# kbench [![CircleCI](https://circleci.com/gh/keichi/kbench.svg?style=svg)](https://circleci.com/gh/keichi/kbench)

## Installation

Currently, kbench is available on TestPyPI.

```
$ pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple kbench
```

## Usage

### pod-throughput

Launch multiple pods in parallel and measure their startup and cleanup time.

```
$ kbench pod-throughput
```

- `-n`, `--num-pods`: Number of pods to launch.
- `-i`, `--image`: Container image to use.

### pod-latency

Launch multiple pods sequentially and measure their startup and cleanup time.

```
$ kbench pod-latency
```

- `-n`, `--num-pods`: Number of pods to launch.
- `-i`, `--image`: Container image to use.

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
