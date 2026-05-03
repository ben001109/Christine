from christine.gui.app import GuiMessage, GuiQueues


def test_gui_queues_store_user_and_assistant_messages():
    queues = GuiQueues()

    queues.submit_user("hello")
    queues.submit_assistant("hi")

    assert queues.next_user() == GuiMessage(role="user", text="hello")
    assert queues.next_assistant() == GuiMessage(role="assistant", text="hi")
