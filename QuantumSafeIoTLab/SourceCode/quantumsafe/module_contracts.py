"""Versioned integration contracts. Descriptions, not claims of implemented integrations.

No arbitrary Python module loading is performed here. This registry is deliberately
static until signed extension packaging and isolation have been implemented.
"""
from dataclasses import dataclass

CONTRACT_VERSION = "1.0"

@dataclass(frozen=True)
class ComponentContract:
    name: str
    input_contract: str
    output_contract: str
    status: str
    admin_controlled: bool = False

COMPONENTS = (
    ComponentContract("virtual_gateway", "authorized lab HTTP requests", "allow/block event", "existing"),
    ComponentContract("edge_rf", "Edge-IIoTset compatible 10-feature records", "binary prediction", "offline_only", True),
    ComponentContract("ml_kem", "authenticated participant integration required", "shared secret", "demo_only"),
    ComponentContract("prolog_reasoning", "normalized security facts", "reasoned explanation", "planned"),
    ComponentContract("model_registry", "verified model package and feature schema", "versioned model metadata", "planned", True),
    ComponentContract("adaptive_learning", "verified labeled evidence", "evaluated candidate model", "planned", True),
    ComponentContract("device_adapter", "supported device/broker observations", "normalized telemetry", "planned"),
)

def get_contract(name: str) -> ComponentContract:
    for component in COMPONENTS:
        if component.name == name:
            return component
    raise KeyError(f"Unknown component: {name}")
