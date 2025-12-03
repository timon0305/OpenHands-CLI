"""
PyInstaller hook for the openhands namespace package.

This hook ensures that only the PyPI packages (openhands.sdk and openhands.tools)
are collected, not the openhands package from /openhands/code.
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

# We only want to collect openhands.sdk and openhands.tools from the virtual environment
# Not the openhands package from /openhands/code
datas = []
binaries = []
hiddenimports = []

# Explicitly collect only SDK and tools subpackages
sdk_datas, sdk_binaries, sdk_hiddenimports = collect_all('openhands.sdk', include_py_files=True)
tools_datas, tools_binaries, tools_hiddenimports = collect_all('openhands.tools', include_py_files=True)

datas.extend(sdk_datas)
datas.extend(tools_datas)
binaries.extend(sdk_binaries)
binaries.extend(tools_binaries)
hiddenimports.extend(sdk_hiddenimports)
hiddenimports.extend(tools_hiddenimports)

# Ensure all submodules are included
hiddenimports += collect_submodules('openhands.sdk')
hiddenimports += collect_submodules('openhands.tools')
