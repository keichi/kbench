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

Create a deployment and measure the time for rescaling its size.

```
$ kbench deployment-scaling
```

- `-i`, `--image`: Container image to use.
- `-m`, `--num-replicas1`: Number of replicas.
- `-n`, `--num-replicas2`: Number of replicas.
