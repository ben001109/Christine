def format_chat_prefix(role: str) -> str:
    if role == "user":
        return "\n🧑 You: "
    if role == "assistant":
        return "\n♡ Christine: "
    return ""
