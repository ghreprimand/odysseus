"""Regression: llama.cpp serve must expose the pip CUDA runtime libs at runtime.

A Linux CUDA build links the wheel's libcudart/libcublas, which install under
site-packages/nvidia/*/lib and are not on the dynamic loader's default path. The
serve flow only exported PATH (bin dirs), never LD_LIBRARY_PATH, so a GPU-built
llama-server could not load the CUDA runtime and fell back to CPU with
"warning: no usable GPU found, --gpu-layers option will be ignored" (#2239).

The serve branch now prepends those wheel lib dirs to LD_LIBRARY_PATH (the
runtime mirror of the build-time PATH/CUDA_HOME export), and the serve-output
diagnosis recognizes the runtime warning (build-time CMake errors were already
covered by #559).
"""
import pathlib

from routes.cookbook_helpers import (
    _append_llama_cpp_serve_cuda_env_lines,
    _diagnose_serve_output,
)

_ROUTES = (
    pathlib.Path(__file__).resolve().parent.parent / "routes" / "cookbook_routes.py"
).read_text(encoding="utf-8")


def test_serve_cuda_env_lines_put_wheel_libs_on_ld_library_path():
    lines = []
    _append_llama_cpp_serve_cuda_env_lines(lines)
    script = "\n".join(lines)
    # Globs the pip CUDA wheel lib dirs (covers cudart/cublas, cu12/cu13 layouts).
    assert "site-packages/nvidia/*/lib" in script
    # Prepends each existing dir to the runtime loader path.
    assert "export LD_LIBRARY_PATH=" in script
    # Only acts when the dir exists, so it is a no-op without the wheels.
    assert '[ -d "$_culib" ]' in script
    # No leading/trailing colon when LD_LIBRARY_PATH was previously unset.
    assert "${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" in script
    # Skipped on macOS, which serves via Metal rather than CUDA.
    assert '[ "$(uname -s)" != "Darwin" ]' in script


def test_serve_branch_exports_cuda_runtime_path():
    # The llama.cpp serve branch must call the helper so the export is in scope
    # when llama-server launches, not only during the one-time source build.
    assert "_append_llama_cpp_serve_cuda_env_lines(runner_lines)" in _ROUTES


def test_serve_diagnosis_recognizes_runtime_gpu_fallback():
    # The serve-time "no usable GPU found" warning must be diagnosed; this is the
    # runtime half that #559 (build-time CMake errors) did not cover.
    diagnosis = _diagnose_serve_output(
        "warning: no usable GPU found, --gpu-layers option will be ignored"
    )
    assert diagnosis is not None
    assert "llama.cpp" in diagnosis["message"]
