NTPE 1.0 Beta — Stage-13.3 Web UI Session Page

Status: PASS

新增 Web UI Session Page，提供 framework-neutral session list、session actions、session summary view model。

相容性：
- 僅透過 External API / REST Session API 存取 session 資訊。
- 不直接依賴 Runtime internals。
- 不修改 frozen REST API / Runtime API / Platform Services。
- 保持 Translation Core 路徑不變。
