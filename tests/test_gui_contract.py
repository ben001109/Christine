from christine.gui.app import GuiMessage, GuiQueues


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
