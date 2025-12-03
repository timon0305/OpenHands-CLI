"""
PyInstaller hook for openhands.sdk package.
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# Collect everything from openhands.sdk
datas, binaries, hiddenimports = collect_all('openhands.sdk', include_py_files=True)

# Explicitly add all submodules
hiddenimports += collect_submodules('openhands.sdk')
