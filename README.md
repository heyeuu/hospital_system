# 医院门诊挂号系统

基于 Streamlit + SQLAlchemy 的门诊挂号项目，强调“前后端解耦 + 业务规则防护 + 数据库约束”三重保障：表示层只做展示与交互，业务层封装规则与事务，数据库层以唯一约束兜底，避免并发与逻辑冲突。

## 功能概览
- 科室、医生、患者的基础信息录入。
- 门诊挂号：校验医生所属科室、时间不能为过去、15 分钟号源冲突检测（含悲观锁），并在数据库层有 `(doctor_id, visit_time)` 和 `(patient_id, visit_time)` 唯一约束。
- 挂号管理：列表筛选（科室/日期/状态）、确认就诊、删除记录。
- 仪表盘：总挂号、已就诊、待就诊的指标卡；科室挂号分布条形图。
- 只读数据库友好：当默认路径不可写时，自动切换到用户目录下的可写副本（`~/.hospital_system/hospital.db`），或可通过环境变量显式指定。

## 项目优点
- **三层防护的预约冲突处理**：15 分钟窗口检查（医生/患者双向）、悲观锁防竞态、数据库唯一约束兜底。
- **逻辑/表示层分离**：Streamlit 只做 UI，业务逻辑集中在 `services.py`，便于测试与替换前端。
- **鲁棒性**：只读数据库自动 fallback；事务失败自动回滚，错误通过自定义异常传递到 UI。
- **可扩展性**：模型/仓储/服务分层清晰，方便接入 REST、RPC 或其他前端。
- **快速体验**：提供 seed 数据和一键启动命令，开箱即可看到仪表盘和挂号流程。

## 环境要求
- Python 3.13
- 依赖：`streamlit`, `sqlalchemy`, `pandas`（开发工具：`black`, `isort`）

## 安装依赖
使用本地 Python 环境（只安装运行依赖）：
```bash
pip install -r <(python - <<'PY'
import json, tomllib, sys
deps = tomllib.load(open("pyproject.toml","rb"))["project"]["dependencies"]
print("\n".join(deps))
PY
)
```
或使用 Poetry（包含开发依赖）：
```bash
poetry install
```

## 数据库路径
- 推荐显式设置到可写目录，例如项目的 `data/`：
```bash
mkdir -p ./data
export HOSPITAL_DB_URL=sqlite:///./data/hospital.db  # 请替换为你的绝对路径
```

- 未设置 `HOSPITAL_DB_URL` 时，默认使用 `<当前工作目录>/data/hospital.db`，若不可写则自动切到 `~/.hospital_system/hospital.db` 并给出警告。

## 初始化演示数据
```bash
export HOSPITAL_DB_URL=sqlite:///./data/hospital.db  # 可选
python -m hospital_system.seed
```
或在虚拟环境中：
```bash
HOSPITAL_DB_URL=sqlite:///./data/hospital.db
POETRY_ACTIVE=1 poetry run python -m hospital_system.seed

```

Seed 会创建科室/医生/患者，并按 30 分钟间隔生成示例挂号，避免唯一约束冲突。

## 运行 Streamlit 前端
```bash
export HOSPITAL_DB_URL=sqlite:///./data/hospital.db  # 确保可写
streamlit run src/hospital_system/presentation/streamlit_app.py
```
或在虚拟环境中：
```bash
HOSPITAL_DB_URL=sqlite:///./data/hospital.db poetry run streamlit run src/hospital_system/presentation/streamlit_app.py
```
打开浏览器中提示的本地地址即可使用。

## 主要业务规则
- 医生与科室一致性校验。
- 预约时间必须晚于当前时间。
- 15 分钟号源冲突检测（含 `SELECT ... FOR UPDATE` 悲观锁）+ 数据库唯一约束双重保护（医生同一时间段唯一、患者同一时间段唯一）。
- 状态为 “已取消” 的记录不参与冲突判断。
- 冲突或只读库写入时，会在界面上展示友好的错误提示。

## 常见问题
- **只读数据库**：确认 `HOSPITAL_DB_URL` 指向可写路径；确保文件和目录权限可写；必要时删除只读文件让程序创建新的可写副本。
- **端口占用**：`streamlit run` 默认 8501，可用 `--server.port 8502` 修改。

## 路径与模块
- 代码位置：`src/hospital_system/`
- 入口：`src/hospital_system/presentation/streamlit_app.py`
- 业务层：`src/hospital_system/services.py`
- ORM 模型：`src/hospital_system/models.py`
- 异常定义：`src/hospital_system/exceptions.py`
- 种子数据：`src/hospital_system/seed.py`
