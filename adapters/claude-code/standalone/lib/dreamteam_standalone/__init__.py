"""DreamTeam standalone Claude Code adapter support."""
from .model import DoctorReport, InstallResult, StandaloneInstallError
from .operations import doctor, install, uninstall

__all__ = [
    "DoctorReport",
    "InstallResult",
    "StandaloneInstallError",
    "doctor",
    "install",
    "uninstall",
]
