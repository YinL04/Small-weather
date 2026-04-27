# 小天气 Agent

一个最小可用的天气出行 agent。用户输入城市后，agent 会调用免费的 `wttr.in` JSON 接口获取实时天气，并返回：

- 当前天气和气温
- 出行建议
- 适合当天安排的旅游景点推荐

## 使用方式

1. 创建虚拟环境并安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果 `python` 命令不存在，请先安装 Python 3.11 或更新版本，并勾选 “Add python.exe to PATH”。

2. 创建环境变量文件：

```powershell
Copy-Item .env.example .env
```

3. 编辑 `.env`。

`OPENAI_API_KEY` 是可选项：填了以后会使用大模型生成更自然的建议；不填也能通过内置规则正常运行。

4. 启动：

```powershell
python -m weather_agent.cli
```

也可以直接传城市：

```powershell
python -m weather_agent.cli 北京
```

## 项目结构

```text
weather_agent/
  agent.py      # Agent 编排：天气工具 + 建议生成 + 景点推荐
  cli.py        # 命令行入口
  config.py     # .env 配置读取
  tools.py      # wttr.in 天气查询工具
```
