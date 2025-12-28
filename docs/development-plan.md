
# Python Photo Organizer – Development Plan
# Python 照片整理器开发计划

## 1. Objectives & Scope
## 1. 项目目标与范围
- Build a CLI-first Python app that organizes photos from a source directory into a target directory tree grouped by capture year/month (`YYYY/M`).
- 构建一个以命令行为主的 Python 应用，将源目录中的图片按拍摄年份和月份整理到 `YYYY/M` 结构的目标目录。
- Preserve EXIF metadata when available; fall back to file creation timestamps when EXIF is missing.
- 优先使用 EXIF 拍摄时间，缺失时回退到文件创建时间。
- Provide a resilient workflow that reports progress, handles errors gracefully, and produces an HTML summary report with media previews and links.
- 提供可视进度、稳健错误处理，并生成带预览与链接的 HTML 报告的可靠流程。

## 2. Functional Requirements
## 2. 功能需求
1. **Input Handling**
1. **输入处理**
   - Accept CLI args or config for source, destination, dry-run, HTML report path, logging level.
   - 支持通过命令行或配置指定源目录、目标目录、试运行开关、HTML 报告路径与日志级别。
   - Validate directories and permissions before execution.
   - 执行前检查目录存在性与写权限。
2. **Photo Discovery**
2. **照片扫描**
   - Recursively traverse the source directory.
   - 递归遍历源目录。
   - Filter supported formats (JPEG, PNG, HEIC, RAW) with extensible config.
   - 过滤受支持的图片格式（JPEG、PNG、HEIC、RAW），并允许扩展配置。
3. **Metadata Extraction**
3. **元数据提取**
   - Use Pillow/piexif to read `DateTimeOriginal`, `DateTime`, `CreateDate`.
   - 使用 Pillow 或 piexif 读取 `DateTimeOriginal`、`DateTime`、`CreateDate`。
   - Fall back to filesystem creation time when EXIF missing/invalid.
   - 当 EXIF 缺失或无效时回退到文件系统创建时间。
   - Normalize timestamps to timezone-aware `datetime` objects.
   - 将时间戳规范化为带时区的 `datetime` 对象。
4. **Destination Path Resolution**
4. **目标路径计算**
   - Derive `year` and `month` from the chosen timestamp.
   - 从时间戳中拆分年份与月份。
   - Create `<dest>/<year>/<month>` directories on demand.
   - 按需创建 `<dest>/<year>/<month>` 目录。
5. **File Transfer Logic**
5. **文件迁移逻辑**
   - Prefer `shutil.move` for moves.
   - 默认使用 `shutil.move`。
   - Detect name collisions; append suffix or hash to keep unique names.
   - 检测重名并追加序号或哈希以保证唯一性。
   - On move failure (permissions, cross-device) fall back to copy (+ delete if possible).
   - 移动失败（权限、跨设备等）时自动回退到复制并尽可能删除原文件。
6. **Progress & Logging**
6. **进度与日志**
   - Show progress bar (e.g., `tqdm`) with totals, current action, error count.
   - 使用 `tqdm` 显示总量、当前操作与错误计数。
   - Emit structured logs to console and rotating files.
   - 输出结构化日志到控制台与轮转日志文件。
7. **HTML Report Generation**
7. **HTML 报告生成**
   - Summarize moved, copied, renamed, skipped/failed counts.
   - 汇总移动、复制、重命名、跳过/失败的数量。
   - Provide sections for moved samples, renamed files (with `file://` links + thumbnails), copied files, failures with reasons.
   - 展示移动样例、重命名文件（含 `file://` 链接与缩略图）、复制文件及失败原因。
   - Embed lightweight CSS for offline readability.
   - 内嵌轻量 CSS 以保证离线可读。
8. **Error Handling**
8. **错误处理**
   - Wrap file operations in try/except to keep pipeline running.
   - 用 try/except 包裹文件操作以保证流程不断。
   - Classify metadata/IO/permission errors for reporting.
   - 将错误按元数据、IO、权限等分类记录。
   - Retry transient issues (e.g., sharing violation) with back-off.
   - 对临时错误（如共享冲突）采用退避重试。

## 3. Non-Functional Requirements
## 3. 非功能性需求
- Compatible with Python 3.10+.
- 兼容 Python 3.10 及以上。
- Sustain ≥10k photos without crashes; keep memory low via streaming.
- 稳定处理不少于 1 万张照片，并通过流式处理控制内存。
- Provide unit/integration tests for metadata, path resolver, collision handler, report generator.
- 为元数据、路径解析、重名处理、报告生成提供单元与集成测试。
- Allow configurable logging location and verbosity.
- 支持配置日志位置与详细程度。

## 4. Architecture Overview
## 4. 架构概览
- `cli.py`: Parse arguments, validate input, wire dependencies.
- `cli.py`：解析参数、校验输入并装配依赖。
- `scanner.py`: Walk source tree and yield candidate files.
- `scanner.py`：遍历源目录并输出候选文件。
- `metadata.py`: Extract EXIF/FS timestamps with fallbacks.
- `metadata.py`：读取 EXIF 或文件系统时间并提供回退。
- `organizer.py`: Build destination directories and unique filenames.
- `organizer.py`：生成目标目录并确保文件名唯一。
- `transfer.py`: Execute move/copy, handle collisions and retries.
- `transfer.py`：执行移动或复制，处理重名与重试。
- `progress.py`: Render progress bar and metrics.
- `progress.py`：展示进度条与统计数据。
- `report.py`: Collect run stats and render HTML report.
- `report.py`：汇总运行信息并生成 HTML 报告。
- `logger.py`: Configure shared structured logging.
- `logger.py`：提供共享的结构化日志配置。
- Data flow: CLI → Scanner → Metadata → Organizer → Transfer → Report/Logging.
- 数据流：CLI → Scanner → Metadata → Organizer → Transfer → Report/Logging。

## 5. Detailed Workflow
## 5. 详细流程
1. Initialize logging, load config, and prepare report context.
1. 初始化日志、加载配置并准备报告上下文。
2. Scan the source directory to build a list/generator and count for progress.
2. 扫描源目录以生成列表或生成器并统计数量供进度条使用。
3. For each file:
3. 针对每个文件：
   - Extract timestamp via `metadata.get_capture_datetime(path)`.
   - 调用 `metadata.get_capture_datetime(path)` 获取标准化时间戳。
   - Build destination path via `organizer.build_destination(timestamp, dest_root)`.
   - 通过 `organizer.build_destination(timestamp, dest_root)` 构建目标路径。
   - Ensure directories exist using `Path.mkdir(parents=True, exist_ok=True)`.
   - 使用 `Path.mkdir(parents=True, exist_ok=True)` 确保目录存在。
   - Resolve filename collisions with `organizer.ensure_unique_name(dest_dir, candidate_name)`.
   - 借助 `organizer.ensure_unique_name(dest_dir, candidate_name)` 解决重名。
   - Attempt move; if it fails, try copy and classify result (moved/copied/failed, renamed flag).
   - 首选移动，失败则复制，并记录结果类型（移动/复制/失败及重命名标记）。
   - Update progress UI and report tracker with metadata + relative paths.
   - 用元数据与相对路径更新进度 UI 和报告跟踪。
4. After processing, call `report.render(html_path)` to output the HTML summary.
4. 全部完成后调用 `report.render(html_path)` 生成 HTML 总结。

## 6. Progress & UX Details
## 6. 进度与体验细节
- Use `tqdm` with custom format to display action, filename, counts.
- 使用自定义格式的 `tqdm` 显示操作、文件名与计数。
- Offer `--quiet` flag to suppress progress output.
- 提供 `--quiet` 选项以关闭进度输出。
- Emit periodic summaries (every N files) for log ingestion.
- 每处理 N 个文件输出一次摘要便于日志分析。

## 7. HTML Report Outline
## 7. HTML 报告结构
```html
<!DOCTYPE html>
<!-- 文档类型声明 -->
<html>
<!-- HTML 根节点 -->
<head>
  <meta charset="utf-8" />
  <!-- 使用 UTF-8 编码 -->
  <title>Photo Organizer Report</title>
  <!-- 照片整理报告标题 -->
  <style>
    body { font-family: Arial, sans-serif; margin: 2rem; }
    /* 页面主体样式 */
    .metrics { display: flex; gap: 1rem; }
    /* 指标区域布局 */
    .thumb { max-height: 120px; }
    /* 缩略图尺寸 */
    table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
    /* 表格布局 */
    th, td { border: 1px solid #ddd; padding: 0.5rem; }
    /* 表头与单元格样式 */
  </style>
</head>
<body>
  <h1>Summary</h1>
  <!-- 总览 -->
  <!-- metrics cards -->
  <!-- 指标卡片 -->
  <section id="renamed">...</section>
  <!-- 重命名板块 -->
  <section id="copied">...</section>
  <!-- 复制板块 -->
  <section id="failed">...</section>
  <!-- 失败板块 -->
</body>
</html>
```
- Each table row should list original path, new path (hyperlinked), reason (renamed/copied/failed), plus a thumbnail `<img>` pointing to the destination file.
- 每行需包含原路径、新路径（超链接）、原因（重命名/复制/失败）以及指向目标文件的 `<img>` 缩略图。

## 8. Error & Retry Strategy
## 8. 错误与重试策略
- Log metadata failures, fall back to filesystem timestamps, and mark failures when no timestamp is available.
- 元数据读取失败时记录日志，回退到文件系统时间，若仍不可用则标记失败。
- Retry transfer errors such as `PermissionError` up to two times with exponential back-off; preserve originals on persistent failure.
- 对 `PermissionError` 等迁移错误最多退避重试两次，若继续失败则保留原文件。
- Maintain structured `ReportItem` entries capturing status and root causes.
- 维护结构化的 `ReportItem` 列表记录状态与根因。

## 9. Testing Plan
## 9. 测试计划
- Use pytest for metadata edge cases, destination formatting, collision resolution, and HTML report snapshot tests.
- 使用 pytest 针对元数据边界、路径格式、重名处理和 HTML 报告快照进行测试。
- Run integration tests with temporary directories and sample images to verify end-to-end moves and report content.
- 通过临时目录与示例图片执行端到端集成测试，验证迁移与报告内容。

## 10. Milestones
## 10. 里程碑
1. **Week 1** – Project scaffolding, CLI, logging, scanner, metadata extraction.
1. **第 1 周**——完成脚手架、CLI、日志、扫描器与元数据模块。
2. **Week 2** – Destination resolver, transfer logic, collision handling, fallbacks.
2. **第 2 周**——实现目标路径解析、迁移逻辑、重名与回退策略。
3. **Week 3** – Progress UI, HTML reporter, dry-run support.
3. **第 3 周**——完善进度 UI、HTML 报告与试运行支持。
4. **Week 4** – Comprehensive testing, documentation, packaging instructions.
4. **第 4 周**——完成全面测试、文档与打包说明。

## 11. Open Questions / Next Steps
## 11. 未决问题与后续计划
- Decide on thumbnail generation for large RAW files (downscaled copies vs. on-demand rendering).
- 确定大体积 RAW 文件的缩略图策略（预生成下采样或按需渲染）。
- Evaluate supporting video formats (MP4, MOV) as a stretch goal.
- 评估将 MP4、MOV 等视频格式纳入扩展目标的可行性。
- Define localization needs for report text and UI strings.
- 明确报告文本与界面字符串的本地化需求。
