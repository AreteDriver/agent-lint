# Installation

## PyPI (Recommended)

```bash
pip install agentlinter
```

Requires Python 3.11 or newer.

## Docker

```bash
docker pull ghcr.io/aretedriver/agent-lint:latest
```

Run the container:

```bash
docker run --rm -v "$(pwd):/work" ghcr.io/aretedriver/agent-lint lint /work/workflows/
```

## From Source

```bash
git clone https://github.com/AreteDriver/agent-lint.git
cd agent-lint
pip install -e .
```

## Verify Installation

```bash
agent-lint --version
```
