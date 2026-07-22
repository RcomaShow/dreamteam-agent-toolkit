"""DreamTeam 0.4.2 usability and hardened cost-proof orchestration primitives."""
from .config import Profile, RuntimeCapabilities, RuntimeConfig, Topology
from .pricing import ExecutionLane, PriceBook, TokenUsage, estimate_cost, resolve_model
from .routing import Criticality, Route, RouteDecision, RouteRequest, TaskKind, choose_route

__all__ = [
    "RuntimeCapabilities",
    "RuntimeConfig",
    "Topology",
    "Profile",
    "ExecutionLane",
    "PriceBook",
    "TokenUsage",
    "estimate_cost",
    "resolve_model",
    "Criticality",
    "TaskKind",
    "Route",
    "RouteDecision",
    "RouteRequest",
    "choose_route",
]
__version__ = "0.4.2"
