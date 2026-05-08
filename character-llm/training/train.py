"""Training entrypoint for fine-tuning the character LLM."""

import yaml


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def train():
    config = load_config("config.yaml")
    print("Loaded training config:", config)
    print("Starting training loop... (placeholder)")


if __name__ == "__main__":
    train()
