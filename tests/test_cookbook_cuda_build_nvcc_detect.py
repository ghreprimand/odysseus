"""Regression for #2377: the llama.cpp build must detect a pip-installed nvcc
no matter where pip put the CUDA wheels.

The build-time detector used to glob only ~/.local/lib/python*/site-packages.
A GPU host that installed the CUDA wheels as root inside a Docker image (so the
wheels land in /usr/local/lib/.../dist-packages, not ~/.local) was therefore
told "no HIP/CUDA toolchain found" and got a CPU-only build. The fix searches
the per-user and system trees, and both the site-packages and dist-packages
layouts.
"""
import shlex
import subprocess
import textwrap
from pathlib import Path

from routes.cookbook_helpers import _append_llama_cpp_linux_accel_build_lines


def _detection_block() -> str:
    """The generated `for _cubase ... done` nvcc-detection shell, as one string."""
    lines: list[str] = []
    _append_llama_cpp_linux_accel_build_lines(lines)
    start = next(i for i, ln in enumerate(lines) if "for _cubase in" in ln)
    done_seen = 0
    end = start
    for i in range(start, len(lines)):
        end = i
        if lines[i].strip() == "done":
            done_seen += 1
            if done_seen == 2:  # the outer `done` closes the detection block
                break
    return "\n".join(lines[start : end + 1])


def test_build_nvcc_detection_searches_user_and_system_layouts():
    block = _detection_block()
    # per-user tree preserved (no regression) ...
    assert "~/.local" in block
    assert "site-packages/nvidia/cuda_nvcc" in block
    # ... plus the system trees a root/Docker install uses ...
    assert "/usr/local" in block
    assert " /usr;" in block or " /usr " in block
    # ... and the Debian/Ubuntu dist-packages layout.
    assert "dist-packages/nvidia/cuda_nvcc" in block
    assert "lib/python3/dist-packages/nvidia/cu12" in block
    # still keys off an executable nvcc and exports the same vars.
    assert '[ -x "$_cudir/bin/nvcc" ]' in block
    assert 'export CUDA_HOME="$_cudir"' in block
    assert "break 2" in block


def _run_detection(bases: list[str], block: str) -> str:
    """Run the real detection block with its base list swapped for a sandbox."""
    rebased = block.replace("~/.local /usr/local /usr", " ".join(shlex.quote(b) for b in bases))
    script = rebased + '\necho "CUDA_HOME=$CUDA_HOME"'
    out = subprocess.run(["bash", "-c", script], capture_output=True, text=True).stdout
    line = next((l for l in out.splitlines() if l.startswith("CUDA_HOME=")), "CUDA_HOME=")
    return line[len("CUDA_HOME=") :]


def test_build_nvcc_detection_finds_dist_packages_nvcc(tmp_path: Path):
    # Mirror the #2377 repro: empty per-user tree, real nvcc in a *system*
    # dist-packages tree (where `pip install` as root drops the wheels).
    user = tmp_path / "user"
    (user / "lib/python3.12/site-packages/nvidia").mkdir(parents=True)
    system = tmp_path / "system"
    nvcc_dir = system / "lib/python3.12/dist-packages/nvidia/cuda_nvcc/bin"
    nvcc_dir.mkdir(parents=True)
    nvcc = nvcc_dir / "nvcc"
    nvcc.write_text("#!/bin/sh\necho nvcc\n")
    nvcc.chmod(0o755)

    block = _detection_block()
    found = _run_detection([str(user), str(system)], block)
    assert found == str(system / "lib/python3.12/dist-packages/nvidia/cuda_nvcc"), found

    # Negative control: the old user-only / site-packages-only form misses it.
    old = textwrap.dedent(
        f"""
        for _cudir in {shlex.quote(str(user))}/lib/python*/site-packages/nvidia/cu13 \
                      {shlex.quote(str(user))}/lib/python*/site-packages/nvidia/cu12 \
                      {shlex.quote(str(user))}/lib/python*/site-packages/nvidia/cuda_nvcc; do
          [ -x "$_cudir/bin/nvcc" ] && export CUDA_HOME="$_cudir" && break
        done
        echo "CUDA_HOME=$CUDA_HOME"
        """
    )
    out = subprocess.run(["bash", "-c", old], capture_output=True, text=True).stdout
    assert "CUDA_HOME=\n" in out + "\n", "old detector should have found nothing"
