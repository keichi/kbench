# kbench

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
