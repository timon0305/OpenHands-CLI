"""
PyInstaller hook for openhands.tools package.
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect everything from openhands.tools
datas, binaries, hiddenimports = collect_all('openhands.tools', include_py_files=True)

# Explicitly add all submodules
hiddenimports += collect_submodules('openhands.tools')
