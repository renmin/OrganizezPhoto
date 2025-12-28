
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
   - When the HTML report path is omitted, default to saving the report inside the source folder (e.g., `source/organize-report.html`).
   - 若未指定 HTML 报告路径，则默认写入源目录（例如 `source/organize-report.html`）。
   - Validate directories and permissions before execution.
   - 执行前检查目录存在性与写权限。
2. **Media Discovery**
2. **媒体扫描**
   - Recursively traverse the source directory.
   - 递归遍历源目录。
   - Filter supported image formats (JPEG, PNG, HEIC, RAW) and video formats (MP4, MOV, HEVC) with extensible config.
   - 过滤受支持的图片格式（JPEG、PNG、HEIC、RAW）与视频格式（MP4、MOV、HEVC），并允许扩展配置。
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
   - Before moving, compute a hash (e.g., SHA-256) and compare against files already in the target path; treat identical hashes as duplicates and skip moving.
   - 移动前计算哈希（如 SHA-256）并与目标路径已存在文件比对，若哈希一致则视为重复并跳过移动。
   - Maintain destination-specific hash indexes persisted on disk (e.g., JSON/SQLite manifest) and mirrored in memory so duplicate checks reuse cached hashes instead of rescanning every file.
   - 为每个目标目录维护落盘的哈希索引（如 JSON/SQLite 清单）并映射到内存，借助缓存结果完成重复检测，避免反复扫描所有文件。
   - Build each destination folder’s hash cache lazily the first time that folder is touched, then update it incrementally as files move in.
   - 采用延迟加载策略：首次访问某目标目录时才构建其哈希缓存，并在文件迁入时增量更新，以降低整体 I/O。
   - Apply the same hashing, collision, and transfer rules to video files so photos/videos share a unified pipeline.
   - 对视频文件沿用同样的哈希、重名与迁移规则，保持照片与视频的统一流程。
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
   - 展示移动样例、重命名文件（含 `file://` 链接与原文件预览）、复制文件、以及失败与跳过原因。
   - Ensure all narrative text in the HTML report is written in Chinese for consistency.
   - 报告中的说明文字全部使用中文，保持一致的用户体验。
   - Reference the original media files directly for previews (`<img src="...">` for photos, `<video src="..." controls>` for videos) without generating separate thumbnails.
   - 预览直接引用原始媒体文件（照片用 `<img src="...">`，视频用 `<video src="..." controls>`），无需额外生成缩略图。
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
9. **Test Data Generator**
9. **测试数据生成工具**
   - Provide a helper command that randomly copies a specified number of photos/videos (default 100) from a seed directory into a dedicated test source folder.
   - 提供一个辅助命令，从指定种子目录随机拷贝若干（默认 100）张照片或视频到测试源目录。
   - Support CLI flags for seed path, destination test folder, media count, and optional filters so QA can quickly prepare test batches.
   - 支持通过命令行指定种子路径、测试目录、拷贝数量及可选过滤条件，便于快速生成测试数据。

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
- `testdata.py`: Randomly sample media files into test source folders for QA scenarios.
- `testdata.py`：将媒体文件随机采样至测试源目录，支持 QA 场景。
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
   - Load (or lazily build) the destination folder’s hash cache before duplicate comparison, and always persist updates so future runs can reuse the data.
   - 在重复检测前加载（或延迟构建）目标目录的哈希缓存，并在更新后立即持久化，确保后续运行可以复用。
   - Before moving, compare hashes to detect duplicates; skip duplicates and classify as "skipped-duplicate" with context.
   - 移动前比对哈希以检测重复，若重复则跳过并记录为“skipped-duplicate”及相关信息。
   - Attempt move; if it fails, try copy and classify result (moved/copied/failed, renamed flag).
   - 首选移动，失败则复制，并记录结果类型（移动/复制/失败及重命名标记）。
   - Update progress UI and report tracker with metadata + relative paths.
   - 用元数据与相对路径更新进度 UI 和报告跟踪。
4. After processing, call `report.render(html_path)` to output the HTML summary.
4. 全部完成后调用 `report.render(html_path)` 生成 HTML 总结。
   - Resolve `html_path` to the user-provided location or fall back to `<source>/organize-report.html` when unspecified.
   - 若用户未提供报告路径，则回退到 `<source>/organize-report.html` 作为输出位置。

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
   <section id="skipped-duplicates">...</section>
   <!-- 重复跳过板块 -->
  <section id="failed">...</section>
  <!-- 失败板块 -->
</body>
</html>
```
- Each table row should list original path, new path (hyperlinked), reason (renamed/copied/failed), plus a thumbnail `<img>` pointing to the destination file.
 - Each table row should list original path, new path (hyperlinked or destination reference), reason (renamed/copied/failed/skipped-duplicate), and an inline preview referencing the original media (`<img>` for photos, `<video>` for videos).
 - 每行需包含原路径、新路径（或目标引用的超链接）、原因（重命名/复制/失败/重复跳过），并直接嵌入指向原文件的预览（照片用 `<img>`，视频用 `<video>`）。

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
- Leverage the test data generator to quickly assemble randomized media batches for regression suites.
- 利用测试数据生成工具快速构建随机媒体样本，支撑回归测试。

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
- Determine whether additional video formats (e.g., AVI, MKV) or optional transcoding workflows are needed beyond the core set.
- 评估是否需要在现有格式之外支持更多视频格式（如 AVI、MKV）或引入可选的转码流程。
- Plan for future multi-language report support should non-Chinese exports become necessary.
- 若未来需要非中文导出，需规划多语言报告的支持方案。
