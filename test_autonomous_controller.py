from autonomous_controller import (
    evaluate_autonomy
)


class Mock:

    def __init__(self, risk):

        self.risk_level = risk


for level in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):

    result = evaluate_autonomy(
        Mock(level)
    )

    print(level)
    print(result)
    print()