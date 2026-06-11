# Windows 便携打包方案计划

## Summary

目标是把当前 `family-exam-helper` 打包成“仅 Windows、解压即用、双击 EXE 启动”的便携版分发包。推荐方案为：

- 使用 `PyInstaller` 生成 **one-folder** 目录式发布包，而不是 one-file 单文件包。
- 将 `templates/`、`static/` 等只读程序资源打进发布包。
- 将 `banks/`、`uploads/`、`bank_assets/`、`imports/`、`scoring_config.json` 作为 **用户可写数据目录** 放在 EXE 同级目录。
- 提供一个专用启动入口，使用户双击 `FamilyExamHelper.exe` 后自动启动本地 Flask 服务并打开浏览器。

这样做的目标是：

- 用户无需安装 Python、pip、依赖包。
- 用户只需解压后双击运行。
- 题库数据库和图片资源保存在发布目录中，不受临时解压目录影响。
- 后续升级时，可替换程序文件，同时尽量保留用户数据目录。

## Current State Analysis

### 现有运行方式

- 主程序集中在 `app.py`，使用 Flask + SQLite + `openpyxl`。
- 当前启动方式依赖 `start.bat`：
  - 检查本机 Python
  - 按需执行 `pip install -r requirements.txt`
  - 打开浏览器
  - 运行 `python app.py`
- 这与“用户不关心环境、解压即用”的目标不一致，因为仍依赖本机 Python 环境。

### 当前资源与目录假设

`app.py` 当前使用以下基于源码目录的路径：

- `BASE_DIR = os.path.dirname(os.path.abspath(__file__))`
- `BANKS_DIR = os.path.join(BASE_DIR, 'banks')`
- `UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')`
- `BANK_ASSETS_DIR = os.path.join(BASE_DIR, 'bank_assets')`
- `IMPORTS_DIR = os.path.join(BASE_DIR, 'imports')`
- `SCORING_CONFIG_PATH = os.path.join(BASE_DIR, 'scoring_config.json')`

这在源码运行时是可行的，但对打包后存在两个问题：

1. 程序资源与用户数据没有分层。
2. 打包后如果仍按 `__file__` 推导根目录，可能把可写数据定位到打包内部资源目录，不利于便携分发和升级保留数据。

### 当前需要被打包的程序资源

根据仓库结构，程序运行依赖以下只读资源：

- `templates/`
- `static/css/`
- `static/tinymce/`
- `static/import-template-spec.md`

其中 `templates/` 和 `static/` 是 Flask 页面与前端静态资源的核心依赖，必须纳入发布包。

### 当前需要保留为外部可写数据的内容

根据 `app.py` 和 `.gitignore`，这些目录属于运行时用户数据：

- `banks/`
- `uploads/`
- `bank_assets/`
- `imports/`
- `scoring_config.json`（建议作为可编辑配置保留在 EXE 同级）

这些内容不应打进只读程序资源内部，而应在首次启动时自动创建。

## Assumptions & Decisions

- 目标平台：**仅 Windows**
- 启动方式：**双击 EXE**
- 分发形式：**便携压缩包（ZIP）**
- 构建工具：**PyInstaller**
- 打包模式：**one-folder**

选择 one-folder 的原因：

- 便于携带 `templates/` 和 `static/` 等资源目录。
- 运行时更稳定，不依赖 one-file 的临时解压目录。
- 更适合本项目这种需要长期读写题库、图片、导入文件的本地桌面型 Web 应用。

不采用 one-file 的原因：

- 单文件模式会先解包到临时目录，资源路径与持久化目录处理更复杂。
- 对“数据保存在程序旁边、用户易于备份/迁移”这一目标不友好。

## Proposed Changes

### 1. 调整 `app.py` 的路径解析与运行入口

文件：`app.py`

要做的事：

- 增加“运行根目录”和“资源根目录”分离的逻辑。
- 在源码运行时：
  - 运行根目录 = 项目根目录
  - 资源根目录 = 项目根目录
- 在 PyInstaller 打包运行时：
  - 运行根目录 = `sys.executable` 所在目录
  - 资源根目录 = `sys._MEIPASS` 或等效打包资源目录

实现要点：

- 新增类似 `APP_ROOT`、`RESOURCE_ROOT` 的统一路径变量。
- 用户数据目录基于 `APP_ROOT`：
  - `banks/`
  - `uploads/`
  - `bank_assets/`
  - `imports/`
  - `scoring_config.json`
- Flask 模板和静态目录基于 `RESOURCE_ROOT` 显式传入：
  - `Flask(__name__, template_folder=..., static_folder=...)`
- 避免再直接假设 `templates/`、`static/` 与 `__file__` 同级。

为什么这样改：

- 这是让源码模式和打包模式都稳定运行的关键。
- 也是后续升级覆盖程序文件但保留用户数据的基础。

### 2. 新增独立的 EXE 启动入口

文件：新增 `launcher.py` 或等效启动入口文件

要做的事：

- 把“启动本地 Flask 服务 + 自动打开浏览器”的逻辑从 `start.bat` 的环境依赖中抽离出来。
- 启动入口负责：
  - 选择监听地址和端口（默认 `127.0.0.1:5000`）
  - 延迟打开浏览器
  - 调用 Flask 启动

实现要点：

- 启动时检查端口占用；如 `5000` 被占用，可自动回退到其他端口，或至少给出明确提示。
- 自动打开浏览器地址时，应使用实际监听端口。
- `launcher.py` 作为 PyInstaller 的打包入口，比直接打包 `app.py` 更适合控制启动体验。

为什么这样改：

- 双击 EXE 的体验应由 Python 代码自己保证，而不是继续依赖 `.bat`。
- 便于将来加启动日志、异常提示、端口冲突处理。

### 3. 保留 `start.bat` 作为源码开发入口，不作为最终分发入口

文件：`start.bat`

要做的事：

- 明确保留其“开发/本地调试”用途。
- 不再把它作为最终用户的主要启动方式。
- 如有必要，可调整文案，说明“发布版请双击 EXE”。

为什么这样改：

- `start.bat` 当前仍依赖本机 Python 与 pip，更适合开发者环境。
- 这样可以避免“开发运行方式”和“用户分发方式”混用。

### 4. 新增 PyInstaller 构建配置

文件：新增 `family_exam_helper.spec`（或同类 `.spec` 文件）

要做的事：

- 固化打包规则，避免每次用命令行手敲参数。
- 把以下资源纳入打包：
  - `templates/`
  - `static/`
  - `scoring_config.json`（是否作为外置默认文件，可在构建后复制到输出目录）

实现要点：

- 入口文件使用 `launcher.py`
- 使用 `console=False` 或 `console=True` 取决于用户体验选择：
  - 若希望无黑窗，使用 `console=False`
  - 若希望启动失败时能直接看到报错，初版建议先 `console=True`，稳定后再评估隐藏控制台
- 明确 `datas` 配置，将模板与静态资源正确打包

为什么这样改：

- `.spec` 文件是可重复构建的基础。
- 也方便未来接入图标、版本号、公司名等元信息。

### 5. 新增构建脚本

文件：新增 `build_portable.bat`

要做的事：

- 为开发者提供一键构建命令。
- 流程包括：
  - 清理旧 `build/`、`dist/`
  - 安装/检查 `pyinstaller`
  - 执行 `.spec` 构建
  - 在输出目录补齐初始可写目录：
    - `banks/`
    - `uploads/`
    - `bank_assets/`
    - `imports/`
  - 如目标目录中不存在 `scoring_config.json`，复制默认配置进去
  - 生成最终可压缩分发目录

为什么这样改：

- 构建操作标准化，降低后续重复发布成本。

### 6. 新增发布目录说明文档

文件：新增 `docs/portable-package-guide.md` 或 `README-portable.md`

要做的事：

- 说明最终目录结构，例如：

```text
FamilyExamHelper/
├─ FamilyExamHelper.exe
├─ _internal/                  # PyInstaller 运行库
├─ banks/                      # 用户题库数据库
├─ uploads/                    # 旧资源兼容目录
├─ bank_assets/                # 题库图片资源
├─ imports/                    # 导入临时目录
└─ scoring_config.json         # 计分配置
```

- 说明用户如何使用：
  - 解压
  - 双击 EXE
  - 浏览器自动打开
- 说明如何迁移数据：
  - 备份 `banks/` 与 `bank_assets/`
- 说明升级方式：
  - 替换程序文件时保留用户数据目录

为什么这样改：

- 便于交付给非技术用户，也便于你自己后续发布。

### 7. 可选：新增应用图标与版本信息

文件：新增 `assets/app.ico`、版本资源配置

要做的事：

- 为 EXE 设置图标、产品名、版本号。

为什么这样改：

- 不影响功能，但会显著提升成品感。

## Verification Steps

### 开发侧验证

1. 在源码模式下运行，确认路径调整后仍可正常启动：
   - 首页可打开
   - 题库可创建
   - 富文本编辑器可加载
   - 图片上传与访问正常
   - Excel / 标准模板导入正常
2. 用 PyInstaller 构建便携版目录。
3. 在全新目录中仅保留发布产物，模拟真实用户环境启动。

### 用户体验验证

1. 双击 `FamilyExamHelper.exe`
2. 自动打开浏览器访问本地地址
3. 无需 Python、无需 pip、无需手工创建目录
4. 首次运行后自动生成：
   - `banks/`
   - `uploads/`
   - `bank_assets/`
   - `imports/`
   - `scoring_config.json`（如策略选择为外置）

### 功能回归验证

1. 创建题库并录入题目
2. 上传题干图片并查看显示
3. 进行练习和考试
4. 导出与导入题库
5. 关闭后重新打开，确认数据仍保留

### 发布验证

1. 将最终目录压缩成 ZIP
2. 在另一台未安装 Python 的 Windows 电脑上解压
3. 双击 EXE 验证可直接运行

## Executor Notes

执行实现时建议按以下顺序推进：

1. 先改 `app.py` 的路径体系
2. 再加 `launcher.py`
3. 再补 `.spec` 与构建脚本
4. 最后做真实打包与解压验证

优先保证“路径稳定 + 数据可持久化”，再优化图标、隐藏控制台等体验细节。
