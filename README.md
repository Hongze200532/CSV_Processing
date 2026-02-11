# CSV Variable Plotter (Desktop)

一个基于 **Tkinter + Matplotlib** 的本地桌面应用，用于从多个 CSV 文件中选择变量并绘制 2D 曲线图。  
本项目不使用 Streamlit，直接运行 `app.py` 即可启动原生桌面窗口。

## 下载 APP
- [Download Latest APP (macOS .zip)](https://github.com/Hongze200532/CSV_Processing/releases/latest/download/CSV-Variable-Plotter-macOS.zip)
- [All Releases](https://github.com/Hongze200532/CSV_Processing/releases)

## 这款软件解决什么问题
在实验/测试数据分析中，经常会遇到这些需求：
- 多个数据来源（不同平台、不同文件）要一起对比。
- 想快速切换 X/Y 变量并立即看到曲线。
- 只看某个数据区间（按比例切片或手动范围）。
- 导出高分辨率图片用于报告。

本软件就是为这类场景设计的轻量桌面工具。

## 核心功能
- 支持创建多个 **Platform**（平台分组）。
- 每个 Platform 下可添加多个 CSV 文件。
- 支持多文件叠加绘图或分子图绘制。
- 支持选择 `X variable` / `Y variable`。
- 支持 `X period` 数据切片：
  - `All`
  - `First 10%`
  - `First 25%`
  - `Middle 50%`
  - `Last 25%`
  - `Last 10%`
  - `Manual Range`（手动输入起止 X）
- `Manual Range` 下若输入值不在 CSV 中，会自动取最近可用值。
- 支持平滑曲线（`Smooth line` + 窗口大小）。
- 支持设置图像显示比例（输入百分比数字）。
- 支持导出 PNG（可设置 `Export DPI`）。

## 界面结构（当前版本）
左侧是悬浮 UI 外壳，内部有并排双栏：
- 数据源栏（Source Bar）：
  - `Platforms`
  - `Choose CSV`
- 主控制栏（Main Bar）：
  - `Variables & Mode`
  - `X Period`
  - `Render & Export`

右侧是图像显示区域（当前版本已移除数据预览区）。

## 使用流程
1. 在 `Platforms` 中输入平台名并点击 `Add Platform`。  
2. 在 `Current platform` 选择目标平台。  
3. 点击 `Choose CSV(s)`，把该平台需要的 CSV 加进去。  
4. 选择 `X variable` 和 `Y variable`。  
5. 选择 `Plot mode`：
   - `Overlay (One Chart)`：所有来源画在一张图上。
   - `Separate Subplots`：每个来源单独子图。  
6. 选择 `X period`（按比例切片或 `Manual Range`）。  
7. （可选）开启平滑并设置窗口大小。  
8. 输入 `Display size (%)`（例如 `85`），控制图像在右侧区域中的显示尺寸。  
9. 点击 `Plot` 绘图。  
10. 需要导出时设置 `Export DPI`，点击 `Export Plot PNG`。

## 参数说明
- `Plot mode`
  - `Overlay (One Chart)`：用于直接比较不同来源曲线。
  - `Separate Subplots`：避免多条线重叠，便于逐个观察。
- `X period`
  - 百分比选项按行索引范围切片。
  - `Manual Range` 根据 X 列类型自动判断：
    - 数值型：按最近数值匹配。
    - 时间型：按最近时间匹配。
- `Smooth line`
  - 对 Y 值应用滚动平均，窗口越大越平滑。
- `Display size (%)`
  - 控制图像显示区域大小（范围约 40%~100%）。
  - 仅改变显示尺寸，不改变导出分辨率。
- `Export DPI`
  - 控制导出 PNG 清晰度，适合论文/报告排版。

## 数据组织规则（很重要）
- 代码内部采用 `Platform -> 多个 CSV` 进行管理。
- 绘图时会汇总所有已加载数据源进行比较。
- 新增 CSV 时，系统会检查“所有已加载数据”是否仍有足够公共列用于 X/Y（至少 2 列）。
  - 如果公共列不足，本次新增会被拒绝并提示 `Column mismatch`。
- 同一平台内遇到重名文件会自动改名（如 `file (2).csv`）。

## 安装与运行
```bash
cd /Users/lin/Desktop/CSV_Processing
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

## 依赖
- `pandas>=2.0.0`
- `matplotlib>=3.8.0`
- `pyobjc-framework-Cocoa>=10.0`（仅 macOS，用于原生毛玻璃效果）

## 常见问题
### 1) 为什么添加 CSV 后提示 Column mismatch？
因为新文件与当前已加载文件之间没有足够公共列（至少 2 列）可用于 X/Y。请检查列名是否一致。

### 2) 为什么图像看起来太大/太小？
在 `Display size (%)` 输入百分比（如 `75`、`90`），按回车或切换焦点即可生效。

### 3) 为什么右侧有毛玻璃效果？
这是 macOS 下的原生视觉效果；在未绘图状态下会显示毛玻璃覆盖层。

### 4) 本项目是不是网页应用？
不是。它是本地桌面应用，不需要 `streamlit run`。

## 项目文件
- `app.py`：主程序（UI、CSV 加载、绘图、导出逻辑）
- `requirements.txt`：依赖列表
- `README.md`：项目说明文档
