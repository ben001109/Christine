from __future__ import annotations

from collections.abc import Callable


def _missing_dependency(name: str):
    raise RuntimeError(f"GUI command dependency is missing: {name}")


def handle_gui_command(
    command: str,
    *,
    ask: Callable[[str], str],
    understand_image: Callable[[str], str] | None = None,
    generate_image_style: Callable[[str, str], str] | None = None,
) -> str:
    if command.startswith("__IMAGE__"):
        if understand_image is None:
            _missing_dependency("understand_image")
        path = command[9:]
        desc = understand_image(path)
        return ask("老闆傳了一張圖片給你看，內容是：" + desc + "，幫老闆分析或描述這張圖片。")
    if command.startswith("__GENIMAGE__"):
        if generate_image_style is None:
            _missing_dependency("generate_image_style")
        parts = command[12:].split("||")
        prompt = parts[0]
        style = parts[1] if len(parts) > 1 else "realistic"
        result = generate_image_style(prompt, style)
        return ask("圖片生成結果：" + result)
    if command == "__SCREENCAP__":
        return ask("幫老闆分析目前螢幕上的畫面")
    return ask(command)


def process_next_gui_command(queues, **dependencies) -> bool:
    command = queues.next_command()
    if command is None:
        return False
    try:
        reply = handle_gui_command(command, **dependencies)
    except Exception as exc:
        reply = "err:" + str(exc)
    queues.submit_output(reply)
    return True


def run_gui_command_listener(
    queues,
    *,
    sleep: Callable[[float], None],
    should_continue: Callable[[], bool] | None = None,
    interval: float = 0.1,
    **dependencies,
) -> None:
    keep_running = should_continue or (lambda: True)
    while keep_running():
        process_next_gui_command(queues, **dependencies)
        sleep(interval)
