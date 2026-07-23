"""Public standalone adapter operations."""
from .doctor_operation import doctor
from .install_operation import install
from .uninstall_operation import uninstall

__all__ = ["doctor", "install", "uninstall"]
