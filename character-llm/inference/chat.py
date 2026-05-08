"""Simple chat interface for the fine-tuned character model."""


def chat(prompt: str) -> str:
    return f"[stub response] Character replies to: {prompt}"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Chat with the fine-tuned character model.")
    parser.add_argument("prompt", help="User prompt")
    args = parser.parse_args()
    print(chat(args.prompt))
