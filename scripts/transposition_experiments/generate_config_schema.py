import json

from transposition_experiment_models import TranspositionExperimentSetConfig

if __name__ == "__main__":
    schema = TranspositionExperimentSetConfig.model_json_schema()
    with open(
        "./scripts/outputs/transposition-experiment-config-schema.json", "w"
    ) as f:
        f.write(json.dumps(schema, indent=2))
