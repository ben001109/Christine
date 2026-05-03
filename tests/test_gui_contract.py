from christine.gui.app import GuiMessage, GuiQueues
from christine.gui.commands import handle_gui_command, process_next_gui_command


def test_gui_queues_store_user_and_assistant_messages():
    queues = GuiQueues()

    queues.submit_user("hello")
    queues.submit_assistant("hi")

    assert queues.next_user() == GuiMessage(role="user", text="hello")
    assert queues.next_assistant() == GuiMessage(role="assistant", text="hi")


def test_gui_queues_store_raw_commands_and_outputs_fifo():
    queues = GuiQueues()

    queues.submit_command("hello")
    queues.submit_command("__SCREENCAP__")
    queues.submit_output("hi")
    queues.submit_output("screen reply")

    assert queues.next_command() == "hello"
    assert queues.next_command() == "__SCREENCAP__"
    assert queues.next_command() is None
    assert queues.drain_outputs() == ["hi", "screen reply"]
    assert queues.drain_outputs() == []


def test_handle_gui_command_routes_plain_text_to_ask():
    calls = []

    def ask(text):
        calls.append(text)
        return "reply"

    reply = handle_gui_command("hello", ask=ask)

    assert reply == "reply"
    assert calls == ["hello"]


def test_handle_gui_command_routes_image_command():
    ask_calls = []

    def ask(text):
        ask_calls.append(text)
        return "image reply"

    def understand_image(path):
        assert path == "photo.png"
        return "一隻貓"

    reply = handle_gui_command("__IMAGE__photo.png", ask=ask, understand_image=understand_image)

    assert reply == "image reply"
    assert ask_calls == ["老闆傳了一張圖片給你看，內容是：一隻貓，幫老闆分析或描述這張圖片。"]


def test_handle_gui_command_routes_generation_and_screen_commands():
    ask_calls = []

    def ask(text):
        ask_calls.append(text)
        return "reply:" + text

    def generate_image_style(prompt, style):
        assert prompt == "cat"
        assert style == "anime"
        return "圖片已生成"

    gen_reply = handle_gui_command(
        "__GENIMAGE__cat||anime",
        ask=ask,
        generate_image_style=generate_image_style,
    )
    screen_reply = handle_gui_command("__SCREENCAP__", ask=ask)

    assert gen_reply == "reply:圖片生成結果：圖片已生成"
    assert screen_reply == "reply:幫老闆分析目前螢幕上的畫面"


def test_process_next_gui_command_moves_reply_to_output_queue():
    queues = GuiQueues()
    queues.submit_command("hello")

    processed = process_next_gui_command(queues, ask=lambda text: "reply:" + text)

    assert processed is True
    assert queues.drain_outputs() == ["reply:hello"]
    assert process_next_gui_command(queues, ask=lambda text: text) is False
