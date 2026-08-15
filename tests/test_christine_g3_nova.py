import christine_g3_frontier as g3
import christine_g3_nova as nova


class FakeRuntime:
    def __init__(self, answers):
        self.answers = list(answers)
        self.i = 0

    def ask(self, user_input):
        answer = self.answers[min(self.i, len(self.answers)-1)]
        self.i += 1
        turn = g3.TurnEnvelope(user_input=user_input)
        turn.contract = g3.TaskContract(
            goal=user_input,
            operation="create",
            output_kind="code",
            language="python",
        )
        return answer, turn


def memory():
    return nova.NOVAMemory(state_path=None)


def test_exact_repeat_is_rejected():
    m = memory(); gate = nova.NOVAGate(m)
    answer = "```python\nprint('hi')\n```"
    m.add("create|code|x", "x", "code", answer)
    v = gate.evaluate("create|code|x", "code", answer)
    assert not v.accepted
    assert v.duplicate_score == 1.0


def test_variable_rename_does_not_evade_ast_gate():
    m = memory(); gate = nova.NOVAGate(m)
    a = """```python
def total(xs):
    s = 0
    for x in xs:
        s += x
    return s
```"""
    b = """```python
def sum_values(items):
    result = 0
    for item in items:
        result += item
    return result
```"""
    m.add("create|code|sum", "sum", "code", a)
    v = gate.evaluate("create|code|sum", "code", b)
    assert not v.accepted
    assert v.duplicate_score >= 0.74


def test_materially_different_code_is_accepted():
    m = memory(); gate = nova.NOVAGate(m)
    a = """```python
def quicksort(a):
    if len(a) <= 1: return a
    p = a[len(a)//2]
    return quicksort([x for x in a if x < p]) + [x for x in a if x == p] + quicksort([x for x in a if x > p])
```"""
    b = """```python
from collections import deque
def bfs(graph, start):
    q = deque([start])
    seen = {start}
    while q:
        node = q.popleft()
        for nxt in graph.get(node, ()):
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return seen
```"""
    m.add("create|code|hard-python", "hard python", "code", a)
    assert gate.evaluate("create|code|hard-python", "code", b).accepted


def test_runtime_blocks_when_generator_cannot_diversify():
    same = """```python
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    p = arr[len(arr)//2]
    return quicksort([x for x in arr if x < p]) + [x for x in arr if x == p] + quicksort([x for x in arr if x > p])
```"""
    rt = nova.NOVARuntime(inner=FakeRuntime([same, same, same, same]), memory=memory(), max_retries=2)
    first, _ = rt.ask("寫一個超難的 python 腳本")
    second, turn = rt.ask("寫一個超難的 python 腳本")
    assert first != second
    assert "阻止" in second
    assert "nova:blocked-repeat" in turn.trace


def test_runtime_selects_different_retry():
    first = """```python
def quicksort(a):
    return a if len(a) <= 1 else quicksort([x for x in a[1:] if x<a[0]])+[a[0]]+quicksort([x for x in a[1:] if x>=a[0]])
```"""
    alternate = """```python
from collections import deque
def bfs(g, s):
    q=deque([s]); seen={s}
    while q:
        u=q.popleft()
        for v in g.get(u,()):
            if v not in seen:
                seen.add(v); q.append(v)
    return seen
```"""
    rt = nova.NOVARuntime(inner=FakeRuntime([first, first, alternate]), memory=memory(), max_retries=2)
    a, _ = rt.ask("寫一個超難的 python 腳本")
    b, turn = rt.ask("寫一個超難的 python 腳本")
    assert a != b
    assert "bfs" in b
    assert any(x.startswith("nova:selected-retry") for x in turn.trace)


def test_text_near_duplicate_is_detected():
    m = memory(); gate = nova.NOVAGate(m)
    a = "目前資料顯示這個人物是一位台灣 coser，並有約三年的 cosplay 經驗。"
    b = "目前的資料顯示，這個人物是一名台灣 coser，而且大約有三年的 cosplay 經驗。"
    m.add("answer|text|person", "person", "text", a)
    assert gate.evaluate("answer|text|person", "text", b).duplicate_score > 0.55


def test_138b_capacity_preserved():
    assert nova.FIVED9A_TOKEN_CAPACITY == 138_000_000_000
