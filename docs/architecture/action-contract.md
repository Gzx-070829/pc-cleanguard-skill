# Action Contract

`ActionRequest` separates machine facts from prose: action type, exact targets,
parameters, requested effect, timestamp, Agent ID, evidence references, and
dry-run state. Each `ActionTarget` carries an identifier, optional Windows path,
metadata, and observed state.

The authorization fingerprint includes the structured action, target, parameters,
effect, and dry-run flag. `agent_reason` and evidence claims remain available for
audit/explanation but are excluded from authorization material. Changing target,
effect, scope, or action parameters requires a new decision.

JSON Schema: `schemas/guard/action_request.schema.json`.

