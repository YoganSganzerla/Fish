from typing import Literal

from pydantic import BaseModel
from pydantic import ValidationError
from pydantic import Field


# ==========================================
# DECISION
# ==========================================

class Decision(BaseModel):

    aerator_1: int = Field(ge=0, le=1)
    aerator_2: int = Field(ge=0, le=1)
    aerator_3: int = Field(ge=0, le=1)

    feeder: int = Field(ge=0, le=1)

    inlet_valve: int = Field(
        ge=0,
        le=100
    )


# ==========================================
# RESPONSE
# ==========================================

class AquaOpsResponse(BaseModel):

    decision: Decision

    risk_level: Literal[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    ]

    reason: str


# ==========================================
# REGRAS OPERACIONAIS
# ==========================================

MIN_DO_FOR_FEEDING = 5.0

MAX_AMMONIA_FOR_FEEDING = 0.30

MAX_VALVE_CHANGE = 20


# ==========================================
# ACTION CLAMPING
# ==========================================

def clamp_value(
    current,
    requested,
    max_delta
):

    if requested > current + max_delta:

        return current + max_delta

    if requested < current - max_delta:

        return current - max_delta

    return requested


# ==========================================
# VALIDADOR
# ==========================================

def validate_response(
    response_dict,
    current_state=None
):

    try:

        validated = AquaOpsResponse(
            **response_dict
        )

        decision = validated.decision

        # ==================================
        # REGRA 1
        # NÃO ALIMENTAR COM OD BAIXO
        # ==================================

        if current_state:

            if (
                current_state["do"]
                < MIN_DO_FOR_FEEDING
                and decision.feeder == 1
            ):
                return {
                    "valid": False,
                    "error":
                    "Feeder proibido: OD baixo"
                }

        # ==================================
        # REGRA 2
        # NÃO ALIMENTAR COM AMÔNIA ALTA
        # ==================================

        if current_state:

            if (
                current_state["ammonia"]
                > MAX_AMMONIA_FOR_FEEDING
                and decision.feeder == 1
            ):
                return {
                    "valid": False,
                    "error":
                    "Feeder proibido: amônia alta"
                }

        # ==================================
        # REGRA 3
        # ACTION CLAMPING DA VÁLVULA
        # ==================================

        if current_state:

            current_valve = (
                current_state["inlet_valve"]
            )

            decision.inlet_valve = clamp_value(
                current=current_valve,
                requested=decision.inlet_valve,
                max_delta=MAX_VALVE_CHANGE
            )

        return {
            "valid": True,
            "data": validated
        }

    except ValidationError as e:

        return {
            "valid": False,
            "error": str(e)
        }


# ==========================================
# TESTE LOCAL
# ==========================================

if __name__ == "__main__":

    current_state = {
        "do": 4.5,
        "ammonia": 0.15,
        "inlet_valve": 40
    }

    sample = {

        "decision": {

            "aerator_1": 1,
            "aerator_2": 1,
            "aerator_3": 0,

            "feeder": 0,

            "inlet_valve": 100
        },

        "risk_level": "MEDIUM",

        "reason": "Teste"
    }

    result = validate_response(
        sample,
        current_state
    )

    print(result)

    if result["valid"]:

        print(
            "\nVálvula corrigida para:",
            result["data"].decision.inlet_valve
        )