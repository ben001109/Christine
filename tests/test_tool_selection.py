from christine.tools.selection import pick_all_tools


def test_pick_all_tools_returns_complete_tool_list_for_any_input():
    all_tools = [{"name": "a"}, {"name": "b"}]

    assert pick_all_tools("hello", all_tools) is all_tools
    assert pick_all_tools("功能", all_tools) is all_tools
    assert pick_all_tools("", all_tools) is all_tools


def test_pick_all_tools_does_not_copy_or_filter_tools():
    all_tools = [{"name": "only"}]

    picked = pick_all_tools("anything", all_tools)

    picked.append({"name": "new"})
    assert all_tools == [{"name": "only"}, {"name": "new"}]
