import sys
import os
import json
import subprocess
import tempfile
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLineEdit, QFileDialog, 
                             QListWidget, QListWidgetItem, QLabel, QProgressBar, 
                             QTextEdit, QCheckBox, QDialog, QFormLayout, QMessageBox,
                             QSplitter, QGroupBox, QComboBox, QFrame, QButtonGroup)
from PySide6.QtCore import Qt, QProcess, QThread, Signal

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

TRANSLATIONS = {
    "zh": {
        "app_title": "AuraTech - Houdini 批量渲染管理器 2026",
        "grp_files": "工程文件列表",
        "btn_add_file": "添加文件",
        "btn_remove_file": "移除选定",
        "btn_clear_files": "清空",
        "btn_load_nodes": "读取所有节点",
        "btn_settings": "⚙ 设置",
        "grp_nodes": "可选渲染节点",
        "btn_all": "全选",
        "btn_none": "全不选",
        "grp_control": "渲染控制",
        "chk_resume": "断点检查 (跳过已存在帧)",
        "chk_continue_on_error": "出错时继续 (跳过失败任务)",
        "grp_override": "帧范围覆盖",
        "chk_override": "启用覆盖",
        "btn_start": "开始批量渲染",
        "btn_stop": "终止渲染",
        "grp_log": "控制台日志",
        "grp_stats": "系统监控",
        "nav_files": "工程文件",
        "nav_nodes": "节点选择",
        "nav_stats": "性能面板",
        "nav_settings": "设置中心",
        "log_wait": "等待任务中...",
        "msg_no_files": ">>> 错误: 请先添加因为 .hip 文件！",
        "msg_reading": "开始批量读取所有工程节点...",
        "msg_read_file": "读取: {} ...",
        "msg_found_nodes": "  -> 找到 {} 个渲染节点。",
        "msg_read_fail": "  -> 内部读取失败: {}",
        "msg_ext_fail": "  -> 外部读取失败: {}",
        "msg_err_hython": ">>> 错误: 缺少 hython 路径配置。",
        "msg_err_int": ">>> 错误: 帧范围必须是整数！",
        "msg_select_nodes": ">>> 请先勾选需要渲染的节点！",
        "msg_queue_start": "队列启动，共 {} 个任务{}。",
        "msg_all_done": ">>> 所有批量任务已完成！",
        "msg_manual_stop": ">>> 渲染已手动停止。",
        "settings_title": "设置",
        "lbl_hython": "Hython 路径:",
        "lbl_lang": "语言 (Language):",
        "btn_browse": "浏览...",
        "btn_save": "保存",
        "btn_cancel": "取消",
        "hint_hython": "提示: 如果您没有直接使用 hython 运行此程序，
必须指定 hython.exe 的路径才能进行节点读取和渲染。",
        "msg_config_updated": "配置已更新。",
        "lbl_start": "Start:",
        "lbl_end": "End:",
        "grp_monitor": "系统状态",
        "lbl_cpu": "CPU:",
        "lbl_mem": "内存:",
        "lbl_gpu": "显卡:",
        "stat_psutil_missing": "未检测到 psutil 库，仅显示 GPU (如有)。"
    },
    "en": {
        "app_title": "AuraTech - Houdini Batch Render Manager 2026",
        "grp_files": "Project Files",
        "btn_add_file": "Add Files",
        "btn_remove_file": "Remove Selected",
        "btn_clear_files": "Clear All",
        "btn_load_nodes": "Read All Nodes",
        "btn_settings": "⚙ Settings",
        "grp_nodes": "Render Nodes",
        "btn_all": "Select All",
        "btn_none": "Select None",
        "grp_control": "Control Panel",
        "chk_resume": "Resume Check (Skip Existing)",
        "chk_continue_on_error": "Continue on Error (Skip Failed)",
        "grp_override": "Frame Range Override",
        "chk_override": "Enable Override",
        "btn_start": "Start Batch Render",
        "btn_stop": "Abort Queue",
        "grp_log": "Console Console",
        "grp_stats": "Live Performance",
        "nav_files": "Projects",
        "nav_nodes": "Nodes",
        "nav_stats": "Stats",
        "nav_settings": "Settings",
        "log_wait": "Sande by...",
        "msg_no_files": ">>> Error: Please add .hip files first!",
        "msg_reading": "Scanning all project files...",
        "msg_read_file": "Reading: {} ...",
        "msg_found_nodes": "  -> Found {} render nodes.",
        "msg_read_fail": "  -> Internal read failed: {}",
        "msg_ext_fail": "  -> External read failed: {}",
        "msg_err_hython": ">>> Error: Missing hython path configuration.",
        "msg_err_int": ">>> Error: Frame range must be integers!",
        "msg_select_nodes": ">>> Please select nodes to render!",
        "msg_queue_start": "Queue started, {} tasks{}.",
        "msg_all_done": ">>> All batch tasks completed!",
        "msg_manual_stop": ">>> Render manually stopped.",
        "settings_title": "Settings",
        "lbl_hython": "Hython Path:",
        "lbl_lang": "Language:",
        "btn_browse": "Browse...",
        "btn_save": "Save",
        "btn_cancel": "Cancel",
        "hint_hython": "Hint: If not running via hython directly,
you must extract the hython.exe path for node reading and rendering.",
        "msg_config_updated": "Configuration updated.",
        "lbl_start": "Start:",
        "lbl_end": "End:",
        "grp_monitor": "System Monitor",
        "lbl_cpu": "CPU:",
        "lbl_mem": "RAM:",
        "lbl_gpu": "GPU:",
        "stat_psutil_missing": "psutil library not found. RAM/CPU hidden."
    }
}


try:
    import hou
    HOU_AVAILABLE = True
except ImportError:
    HOU_AVAILABLE = False

CONFIG_FILE = "config.json"

class MonitorThread(QThread):
                                                               
    stats_signal = Signal(float, float, str, float, str)

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
                                                                             
        while self.running:
            cpu = 0.0
            mem_p = 0.0
            mem_t = "N/A"
            gpu_p = 0.0
            gpu_t = "N/A"

            if PSUTIL_AVAILABLE:
                try:
                    cpu = psutil.cpu_percent(interval=None)                                                               
                                                                               
                    mem = psutil.virtual_memory()
                    used_gb = mem.used / (1024**3)
                    total_gb = mem.total / (1024**3)
                    mem_p = mem.percent
                    mem_t = f"{used_gb:.1f} GB / {total_gb:.1f} GB"
                except:
                    pass
            
            try:
                                                                     
                cmd = ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"]
                
                creationflags = 0x08000000 if os.name == 'nt' else 0
                result = subprocess.run(cmd, capture_output=True, text=True, creationflags=creationflags)
                
                if result.returncode == 0:
                    output = result.stdout.strip().split(',')
                    if len(output) >= 3:
                        gpu_util = float(output[0])
                        gpu_mem_used = float(output[1])
                        gpu_mem_total = float(output[2])
                        
                        gpu_p = gpu_util
                        gpu_t = f"{int(gpu_mem_used)}MB / {int(gpu_mem_total)}MB"
            except:
                pass

            self.stats_signal.emit(cpu, mem_p, mem_t, gpu_p, gpu_t)
            self.msleep(1000)

    def stop(self):
        self.running = False
        self.wait()

class SettingsDialog(QDialog):
    def __init__(self, parent=None, initial_path="", initial_lang="zh"):
        super().__init__(parent)
        self.parent_ref = parent
        self.setWindowTitle(self.t("settings_title") if hasattr(parent, "t") else "Settings")
        self.resize(550, 300)
        self.result_path = initial_path
        self.current_lang = initial_lang
        
        if hasattr(parent, "styleSheet"):
             self.setStyleSheet(parent.styleSheet() + """
                QDialog { background-color: #1a1a26; }
                QLabel { color: rgba(224, 224, 224, 0.8); font-size: 13px; }
                QComboBox { 
                    background-color: rgba(33, 33, 48, 0.4); 
                    color: #ffffff; 
                    border: 1px solid #2d2d3d; 
                    border-radius: 8px; 
                    padding: 8px;
                    min-width: 150px;
                }
                QComboBox::drop-down { border: none; width: 30px; }
                QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 5px solid #7d5fff; }
                QComboBox QAbstractItemView { background-color: #1a1a26; color: #ffffff; selection-background-color: #7d5fff; border: 1px solid #2d2d3d; outline: none; }
             """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        header = QLabel(self.t("settings_title") if hasattr(parent, "t") else "Settings")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff; margin-bottom: 5px;")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignLeft)
        
        self.path_edit = QLineEdit(initial_path)
        self.path_edit.setPlaceholderText("e.g. C:/Program Files/.../bin/hython.exe")
        self.btn_browse = QPushButton(self.t("btn_browse") if hasattr(parent, "t") else "...")
        self.btn_browse.setFixedWidth(80)
        self.btn_browse.clicked.connect(self.browse)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.btn_browse)
        
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("中文 (Chinese)", "zh")
        self.combo_lang.addItem("English", "en")
        idx = 0 if initial_lang == "zh" else 1
        self.combo_lang.setCurrentIndex(idx)
        
        self.lbl_hython = QLabel(self.t("lbl_hython") if hasattr(parent, "t") else "Hython Path:")
        self.lbl_lang = QLabel(self.t("lbl_lang") if hasattr(parent, "t") else "Language:")
        
        form.addRow(self.lbl_hython, path_layout)
        form.addRow(self.lbl_lang, self.combo_lang)
        layout.addLayout(form)
        
        self.lbl_hint = QLabel(self.t("hint_hython") if hasattr(parent, "t") else "")
        self.lbl_hint.setWordWrap(True)
        self.lbl_hint.setObjectName("SubText")
        layout.addWidget(self.lbl_hint)
        
        layout.addStretch()

        btn_box = QHBoxLayout()
        self.btn_save = QPushButton(self.t("btn_save") if hasattr(parent, "t") else "Save")
        self.btn_save.setObjectName("btn_start")                    
        self.btn_save.setFixedWidth(100)
        self.btn_save.clicked.connect(self.accept)
        
        self.btn_cancel = QPushButton(self.t("btn_cancel") if hasattr(parent, "t") else "Cancel")
        self.btn_cancel.setFixedWidth(100)
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_box.addStretch()
        btn_box.addWidget(self.btn_cancel)
        btn_box.addWidget(self.btn_save)
        layout.addLayout(btn_box)

    def t(self, key):
        if hasattr(self.parent_ref, "t"):
            return self.parent_ref.t(key)
        return key
        
        self.update_texts()
        self.combo_lang.currentIndexChanged.connect(self.on_lang_preview)

    def on_lang_preview(self, index):
                                                      
        code = self.combo_lang.currentData()
        self.current_lang = code
        self.update_texts()

    def update_texts(self):
        t = TRANSLATIONS[self.current_lang]
        self.setWindowTitle(t["settings_title"])
        self.lbl_hython.setText(t["lbl_hython"])
        self.lbl_lang.setText(t["lbl_lang"])
        self.btn_browse.setText(t["btn_browse"])
        self.btn_save.setText(t["btn_save"])
        self.btn_cancel.setText(t["btn_cancel"])
        self.lbl_hint.setText(t["hint_hython"])

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select hython.exe", "C:/Program Files/Side Effects Software", "Executables (*.exe)")
        if path:
            self.path_edit.setText(path)

    def get_data(self):
        return self.path_edit.text(), self.combo_lang.currentData()

class RenderManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1100, 850)                               
        self.tasks = []
        self.failed_tasks = []                                
        self.config = self.load_config()
        self.lang = self.config.get("language", "zh")                
        
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.on_task_finished)
        
        self.init_ui()
        self.apply_style()
        self.update_texts()
        self.check_environment()
        
        self.monitor_thread = MonitorThread()
        self.monitor_thread.stats_signal.connect(self.update_monitor)
        self.monitor_thread.start()
        
        if not PSUTIL_AVAILABLE:
            self.log_output.append(self.t("stat_psutil_missing"))

    def closeEvent(self, event):
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.stop()
        super().closeEvent(event)

    def update_monitor(self, cpu, mem, mem_text, gpu, gpu_text):
        if PSUTIL_AVAILABLE:
            self.prog_cpu.setValue(int(cpu))
            self.prog_cpu.setFormat(f"CPU: {cpu:.1f}%")
            
            self.prog_mem.setValue(int(mem))
            self.prog_mem.setFormat(f"RAM: {mem:.1f}% ({mem_text})")
        
        if gpu_text != "N/A":
            self.prog_gpu.setValue(int(gpu))
            self.prog_gpu.setFormat(f"GPU: {gpu:.1f}% ({gpu_text})")
            
            def get_color(val):
                if val < 60: return "#4caf50" 
                if val < 85: return "#ff9800"
                return "#f44336"
            
        else:
            self.prog_gpu.setValue(0)
            self.prog_gpu.setFormat("GPU: N/A")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {"hython_path": "", "language": "zh"}
        return {"hython_path": "", "language": "zh"}

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def t(self, key):
        return TRANSLATIONS[self.lang].get(key, key)

    def update_texts(self):
                                                                   
        self.setWindowTitle(self.t("app_title"))
        
        self.btn_clear_files.setText(self.t("btn_clear_files"))
        self.btn_load.setText(self.t("btn_load_nodes"))
        self.btn_settings.setText(self.t("btn_settings"))
        
        self.btn_all.setText(self.t("btn_all"))
        self.btn_none.setText(self.t("btn_none"))
        
        self.chk_resume.setText(self.t("chk_resume"))
        self.chk_continue_on_error.setText(self.t("chk_continue_on_error"))
        self.chk_override.setText(self.t("chk_override"))
        
        self.btn_start.setText(self.t("btn_start"))
        self.btn_stop.setText(self.t("btn_stop"))
        
        if not self.log_output.toPlainText():
            self.log_output.setPlaceholderText(self.t("log_wait"))

    def create_card(self, title_key, layout_type=QVBoxLayout):
                                                          
        card = QFrame()
        card.setObjectName("Card")
        layout = layout_type(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        header = QLabel(self.t(title_key))
        header.setObjectName("CardHeader")
        layout.addWidget(header)
        
        return card, layout

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.main_content = QFrame()
        self.main_content.setObjectName("MainContent")
        content_layout = QVBoxLayout(self.main_content)
        content_layout.setSpacing(20)

        title_container = QVBoxLayout()
        self.header_title = QLabel("Houdini Render Copilot")
        self.header_title.setObjectName("HeaderTitle")
        self.sub_text = QLabel("Welcome back! Ready for the next masterpiece?")
        self.sub_text.setObjectName("SubText")
        title_container.addWidget(self.header_title)
        title_container.addWidget(self.sub_text)
        content_layout.addLayout(title_container)

        mid_row = QHBoxLayout()
        mid_row.setSpacing(20)

        self.file_card, file_card_layout = self.create_card("grp_files")
        self.file_list_widget = QListWidget()
        
        file_btns = QHBoxLayout()
        self.btn_add_file = QPushButton("+")
        self.btn_add_file.clicked.connect(self.add_files)
        self.btn_remove_file = QPushButton("-")
        self.btn_remove_file.clicked.connect(self.remove_file)
        self.btn_clear_files = QPushButton("Clear")
        self.btn_clear_files.clicked.connect(self.file_list_widget.clear)
        
        file_btns.addWidget(self.btn_add_file)
        file_btns.addWidget(self.btn_remove_file)
        file_btns.addStretch()
        file_btns.addWidget(self.btn_clear_files)
        
        file_card_layout.addWidget(self.file_list_widget)
        file_card_layout.addLayout(file_btns)
        mid_row.addWidget(self.file_card, 2)

        self.node_card, node_card_layout = self.create_card("grp_nodes")
        self.node_list = QListWidget()
        self.node_list.setSelectionMode(QListWidget.NoSelection)
        self.node_list.setObjectName("nodeList")
        
        node_btns = QHBoxLayout()
        self.btn_all = QPushButton("All")
        self.btn_all.clicked.connect(lambda: self.toggle_all(True))
        self.btn_none = QPushButton("None")
        self.btn_none.clicked.connect(lambda: self.toggle_all(False))
        self.btn_load = QPushButton("Scan Nodes")
        self.btn_load.setObjectName("btn_start")                             
        self.btn_load.clicked.connect(self.load_nodes)
        
        node_btns.addWidget(self.btn_all)
        node_btns.addWidget(self.btn_none)
        node_btns.addStretch()
        node_btns.addWidget(self.btn_load)
        
        node_card_layout.addWidget(self.node_list)
        node_card_layout.addLayout(node_btns)
        mid_row.addWidget(self.node_card, 3)

        content_layout.addLayout(mid_row, 3)

        self.log_card, log_card_layout = self.create_card("grp_log")
        self.progress_bar = QProgressBar()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_card_layout.addWidget(self.progress_bar)
        log_card_layout.addWidget(self.log_output)
        content_layout.addWidget(self.log_card, 2)

        self.right_panel = QFrame()
        self.right_panel.setObjectName("RightPanel")
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(25)

        monitor_card, monitor_layout = self.create_card("grp_stats")
        
        def add_stat(label_text, obj_name):
            lbl = QLabel(label_text)
            lbl.setObjectName("SubText")
            prog = QProgressBar()
            prog.setObjectName("prog_monitor")
            prog.setTextVisible(True)
            monitor_layout.addWidget(lbl)
            monitor_layout.addWidget(prog)
            return prog

        self.prog_cpu = add_stat("CPU Usage", "prog_cpu")
        self.prog_mem = add_stat("Memory Usage", "prog_mem")
        self.prog_gpu = add_stat("GPU Usage", "prog_gpu")
        right_layout.addWidget(monitor_card)

        control_card, control_layout = self.create_card("grp_control")
        
        self.chk_resume = QCheckBox()
        self.chk_resume.setChecked(True)
        self.chk_continue_on_error = QCheckBox()
        
        override_card, override_layout = self.create_card("grp_override")
        self.chk_override = QCheckBox()
        self.chk_override.toggled.connect(self.toggle_override)
        
        override_inputs = QHBoxLayout()
        self.input_start = QLineEdit("1")
        self.input_start.setEnabled(False)
        self.input_start.setMaximumWidth(60)
        self.input_end = QLineEdit("100")
        self.input_end.setEnabled(False)
        self.input_end.setMaximumWidth(60)
        self.lbl_start = QLabel("S:")
        self.lbl_end = QLabel("E:")
        
        override_inputs.addWidget(self.lbl_start)
        override_inputs.addWidget(self.input_start)
        override_inputs.addWidget(self.lbl_end)
        override_inputs.addWidget(self.input_end)
        
        override_layout.addWidget(self.chk_override)
        override_layout.addLayout(override_inputs)
        
        control_layout.addWidget(self.chk_resume)
        control_layout.addWidget(self.chk_continue_on_error)
        control_layout.addWidget(override_card)
        control_layout.addStretch()

        self.btn_start = QPushButton("START RENDER")
        self.btn_start.setObjectName("btn_start")
        self.btn_start.setMinimumHeight(55)
        self.btn_start.clicked.connect(self.start_queue)
        
        self.btn_stop = QPushButton("ABORT")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.clicked.connect(self.stop_render)
        
        self.btn_settings = QPushButton("Settings")
        self.btn_settings.clicked.connect(self.open_settings)
        
        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_stop)
        control_layout.addWidget(self.btn_settings)
        
        right_layout.addWidget(control_card)
        right_layout.addStretch()

        main_layout.addWidget(self.main_content, 1)
        main_layout.addWidget(self.right_panel)

    def toggle_override(self, checked):
        self.input_start.setEnabled(checked)
        self.input_end.setEnabled(checked)

    def check_environment(self):
        if not HOU_AVAILABLE and not self.config.get("hython_path"):
            self.log_output.append(self.t("msg_err_hython"))

    def apply_style(self):
                                                     
        self.setStyleSheet("""
            QMainWindow { background-color: #171721; color: #e0e0e0; font-family: 'Inter', 'Segoe UI', sans-serif; }
            QDialog { background-color: #1a1a26; color: #e0e0e0; border-radius: 12px; }
            
            /* Main Containers */
            #MainContent { background-color: #171721; padding: 20px; }
            #RightPanel { background-color: #1a1a26; border-left: 1px solid #2a2a3a; min-width: 280px; }

            /* Card Style */
            QFrame#Card {
                background-color: #212130;
                border-radius: 15px;
                border: 1px solid #2d2d3d;
            }
            QFrame#Card:hover {
                border: 1px solid #3d3d4d;
            }

            /* Headers */
            QLabel#HeaderTitle { font-size: 24px; font-weight: bold; color: #ffffff; padding: 10px 0; }
            QLabel#CardHeader { font-size: 16px; font-weight: 600; color: #7d5fff; margin-bottom: 5px; }
            QLabel#SubText { color: #a4a4b2; font-size: 12px; }

            /* Lists */
            QListWidget { 
                background-color: transparent; 
                color: #e0e0e0; 
                border: none;
                outline: none;
                font-size: 13px;
            }
            QListWidget::item { 
                padding: 12px; 
                background-color: #262638; 
                border-radius: 8px; 
                margin-bottom: 6px; 
            }
            QListWidget::item:selected { 
                background-color: #3b3b55; 
                border: 1px solid #7d5fff; 
            }
            QListWidget::item:hover { background-color: #2d2d42; }

            /* Buttons */
            QPushButton { 
                background-color: rgba(45, 45, 66, 0.4); 
                color: rgba(255, 255, 255, 0.8); 
                border: 1px solid #3d3d5d;
                padding: 10px 20px; 
                border-radius: 10px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: rgba(59, 59, 85, 0.4); border-color: #7d5fff; color: #ffffff; }
            QPushButton:pressed { background-color: rgba(26, 26, 38, 0.4); }
            
            QPushButton#btn_start { 
                background-color: rgba(125, 95, 255, 0.4); 
                color: rgba(255, 255, 255, 0.9); 
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#btn_start:hover { background-color: rgba(108, 72, 255, 0.4); color: #ffffff; }
            
            QPushButton#btn_stop {
                background-color: rgba(61, 33, 42, 0.4);
                color: rgba(255, 77, 77, 0.8);
                border: 1px solid #5d212a;
            }
            QPushButton#btn_stop:hover { background-color: rgba(93, 33, 42, 0.4); color: #ff4d4d; }

            /* Inputs */
            QLineEdit { 
                background-color: #1a1a26; 
                color: #ffffff; 
                border: 1px solid #2d2d3d; 
                padding: 8px; 
                border-radius: 8px;
            }
            QLineEdit:focus { border: 1px solid #7d5fff; }

            /* Progress Bars */
            QProgressBar { 
                border: none; 
                background-color: #1a1a26;
                height: 8px; 
                text-align: center; 
                color: transparent;
                border-radius: 4px;
            }
            QProgressBar::chunk { 
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7d5fff, stop:1 #ae99ff); 
                border-radius: 4px;
            }
            
            /* Monitor Specific Card Progress bars */
            QProgressBar#prog_monitor {
                height: 6px;
                background-color: #262638;
            }
            QProgressBar#prog_monitor::chunk {
                background-color: #32ff7e; /* Health green */
            }

            /* Log area */
            QTextEdit { 
                background-color: #0f0f12; 
                color: #a4a4b2; 
                font-family: 'Consolas', 'Courier New', monospace; 
                border: 1px solid #2d2d3d;
                border-radius: 10px;
                padding: 10px;
                font-size: 12px;
            }

            /* Checkboxes */
            QCheckBox { color: #a4a4b2; spacing: 10px; font-size: 13px; }
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 5px; border: 1px solid #3d3d4d; background: #1a1a26; }
            QCheckBox::indicator:checked { background-color: #7d5fff; border-color: #7d5fff; }

            /* ScrollBars */
            QScrollBar:vertical, QScrollBar:horizontal {
                border: none;
                background: #1a1a26;
                width: 8px;
                height: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #3d3d4d;
                min-height: 20px;
                min-width: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: #7d5fff;
            }
            QScrollBar::add-line, QScrollBar::sub-line,
            QScrollBar::add-page, QScrollBar::sub-page {
                background: none;
                height: 0;
                width: 0;
            }

            /* ComboBox */
            QComboBox { 
                background-color: #1a1a26; 
                color: #ffffff; 
                border: 1px solid #2d2d3d; 
                border-radius: 8px; 
                padding: 8px;
            }
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 5px solid #7d5fff; }
            QComboBox QAbstractItemView { background-color: #1a1a26; color: #ffffff; selection-background-color: #7d5fff; border: 1px solid #2d2d3d; outline: none; }
        """)

    def open_settings(self):
                           
        dialog = SettingsDialog(self, self.config.get("hython_path", ""), self.config.get("language", "zh"))
        if dialog.exec():
            new_path, new_lang = dialog.get_data()
            if new_path and os.path.exists(new_path):
                self.config["hython_path"] = new_path
            
            self.config["language"] = new_lang
            self.lang = new_lang
            
            self.save_config()
            self.update_texts()
            self.log_output.append(self.t("msg_config_updated") + f" Hython = {new_path}")
                         
    def toggle_all(self, state):
        chk_state = Qt.Checked if state else Qt.Unchecked
        for i in range(self.node_list.count()):
            self.node_list.item(i).setCheckState(chk_state)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "Houdini Files (*.hip *.hipnc *.hiplc)")
        if files:
            for f in files:
                                  
                items = [self.file_list_widget.item(i).text() for i in range(self.file_list_widget.count())]
                if f not in items:
                    self.file_list_widget.addItem(f)

    def remove_file(self):
        for item in self.file_list_widget.selectedItems():
            self.file_list_widget.takeItem(self.file_list_widget.row(item))

    def load_nodes(self):
                                              
        file_count = self.file_list_widget.count()
        if file_count == 0:
            self.log_output.append(self.t("msg_no_files"))
            return
        
        self.node_list.clear()
        self.log_output.append(self.t("msg_reading"))
        
        for i in range(file_count):
            hip_path = self.file_list_widget.item(i).text()
            if not os.path.exists(hip_path):
                continue
                
            self.log_output.append(self.t("msg_read_file").format(os.path.basename(hip_path)))
            QApplication.processEvents()

            if HOU_AVAILABLE:
                self._load_nodes_internal(hip_path)
            else:
                self._load_nodes_external(hip_path)

    def _load_nodes_internal(self, hip_path):
        try:
            try:
                hou.hipFile.load(hip_path, suppress_save_prompt=True)
            except hou.LoadWarning:
                pass
                
            rop_nodes = hou.node("/").allSubChildren()
            count = 0
            for node in rop_nodes:
                category = node.type().category().name()
                type_name = node.type().name().lower()
                is_valid = False
                
                if category == "Lop":
                    if "usdrender" in type_name:
                        if "settings" not in type_name and "product" not in type_name and "vars" not in type_name:
                            is_valid = True
                elif category == "Out":
                    if "render" in type_name or "mantra" in type_name or "redshift" in type_name or "arnold" in type_name or "karma" in type_name:
                         is_valid = True

                if is_valid:
                    frame_info = self._extract_frame_parms(node)
                    self._add_node_item(hip_path, node.path(), frame_info)
                    count += 1
            self.log_output.append(self.t("msg_found_nodes").format(count))
        except Exception as e:
            self.log_output.append(self.t("msg_read_fail").format(str(e)))

    def _extract_frame_parms(self, node):
        info = {"trange": 0, "f": (1, 1, 1)}
        try:
            p_trange = node.parm("trange")
            if p_trange:
                info["trange"] = p_trange.eval()
            p_f = node.parmTuple("f")
            if p_f:
                info["f"] = p_f.eval()
        except:
            pass
        return info

    def _load_nodes_external(self, hip_path):
        hython = self.config.get("hython_path")
        if not hython or not os.path.exists(hython):
            self.log_output.append(self.t("msg_err_hython"))
            return

        script_code = """
import sys, json
try:
    import hou
    try:
        hou.hipFile.load(sys.argv[1], suppress_save_prompt=True)
    except hou.LoadWarning:
        pass
        
    nodes_data = []
    for node in hou.node("/").allSubChildren():
        category = node.type().category().name()
        type_name = node.type().name().lower()
        is_valid = False
        
        if category == "Lop":
            if "usdrender" in type_name:
                if "settings" not in type_name and "product" not in type_name and "vars" not in type_name:
                    is_valid = True
        elif category == "Out":
             if "render" in type_name or "mantra" in type_name or "redshift" in type_name or "arnold" in type_name or "karma" in type_name:
                 is_valid = True
        
        if is_valid:
            info = {"path": node.path(), "trange": 0, "f": [1, 1, 1]}
            try:
                p_trange = node.parm("trange")
                if p_trange: info["trange"] = p_trange.eval()
                p_f = node.parmTuple("f")
                if p_f: info["f"] = p_f.eval()
            except:
                pass
            nodes_data.append(info)
            
    print("JSON_START" + json.dumps(nodes_data) + "JSON_END")
except Exception as e:
    print("ERROR:" + str(e))
"""
        try:
            temp_script = "temp_node_reader.py"
            with open(temp_script, "w") as f:
                f.write(script_code)
                
            command = [hython, temp_script, hip_path]
            creationflags = 0x08000000 if os.name == 'nt' else 0
            result = subprocess.run(command, capture_output=True, text=True, creationflags=creationflags)
            
            if os.path.exists(temp_script):
                os.remove(temp_script)
                
            output = result.stdout
            if "JSON_START" in output:
                json_str = output.split("JSON_START")[1].split("JSON_END")[0]
                nodes_data = json.loads(json_str)
                for data in nodes_data:
                    self._add_node_item(hip_path, data["path"], data)
                self.log_output.append(self.t("msg_found_nodes").format(len(nodes_data)))
            else:
                self.log_output.append(self.t("msg_ext_fail").format(output))
        except Exception as e:
            self.log_output.append(self.t("msg_ext_fail").format(str(e)))

    def _add_node_item(self, hip_file, node_path, info):
                                         
        file_name = os.path.basename(hip_file)
        
        range_str = "[Current Frame]" if self.lang == "en" else "[当前帧]"
        if info["trange"] == 1:
            start, end, inc = info["f"]
            range_str = f"[Frame: {int(start)}-{int(end)}]"
            
        display_text = f"[{file_name}] {node_path}  {range_str}"
            
        item = QListWidgetItem(display_text)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Unchecked)
        
        full_data = info.copy()
        full_data["hip_file"] = hip_file
        item.setData(Qt.UserRole, full_data)
        
        self.node_list.addItem(item)

    def start_queue(self):
        self.tasks = []
        
        force_override = self.chk_override.isChecked()
        override_start = 1
        override_end = 1
        if force_override:
            try:
                override_start = int(self.input_start.text())
                override_end = int(self.input_end.text())
            except ValueError:
                self.log_output.append(self.t("msg_err_int"))
                return

        for i in range(self.node_list.count()):
            item = self.node_list.item(i)
            if item.checkState() == Qt.Checked:
                info = item.data(Qt.UserRole)
                task_data = info.copy()
                
                if force_override:
                    task_data["trange"] = 1
                    task_data["f"] = (override_start, override_end, 1)
                
                task_data["resume"] = self.chk_resume.isChecked()
                    
                self.tasks.append(task_data)
        
        if not self.tasks:
            self.log_output.append(self.t("msg_select_nodes"))
            return
        
        msg = " (Override)" if force_override else ""
        self.log_output.append(self.t("msg_queue_start").format(len(self.tasks), msg))
        self.run_next_task()

    def run_next_task(self):
        if not self.tasks:
                                           
            total_failed = len(self.failed_tasks)
            if total_failed > 0:
                self.log_output.append(f">>> Queue Complete - {total_failed} task(s) failed")
                self.log_output.append("    Failed tasks:")
                for task in self.failed_tasks:
                    self.log_output.append(f"    - {task.get('path', 'Unknown')}")
            else:
                self.log_output.append(self.t("msg_all_done"))
            self.progress_bar.setValue(100)
            return
            
        self.progress_bar.setValue(0)
        
        task_info = self.tasks.pop(0)
        self.current_task = task_info                              
        node_path = task_info["path"]
        hip_file = task_info["hip_file"]
        
        self.log_output.append(f"Rendering: {os.path.basename(hip_file)} -> {node_path}")
        
        if HOU_AVAILABLE:
            hython_exe = sys.executable 
        else:
            hython_exe = self.config.get("hython_path")
            if not hython_exe:
                self.log_output.append(self.t("msg_err_hython"))
                return

        bin_dir = os.path.dirname(hython_exe)
        
        if task_info["trange"] == 1:
            start_f, end_f, inc_f = task_info["f"]
        else:
            start_f, end_f, inc_f = (1, 1, 1)                                                                                               
                                                                                        
            pass 

        resume = task_info.get("resume", False)
        
        script_content = f"""
import sys, os, time
import hou

def get_output_path(node):
    # 1. Check direct parameters
    candidates = ["vm_picture", "picture", "outputimage", "sopoutput", "RS_outputFileNamePrefix", "ar_picture"]
    for parm_name in candidates:
        p = node.parm(parm_name)
        if p:
            val = p.eval()
            if val: return val
            
    # 2. Search upstream for 'picture' parameter (specifically for USD/Karma nodes)
    try:
        curr = node
        for _ in range(20): # Depth limit
            inputs = curr.inputs()
            if not inputs: break
            curr = inputs[0]
            if not curr: break
            
            p = curr.parm("picture")
            if p:
                val = p.eval()
                if val: return val
    except:
        pass
    
    return None

def main():
    hip_file = r"{hip_file.replace(os.sep, '/')}"
    node_path = "{node_path}"
    
    start = {start_f}
    end = {end_f}
    inc = {inc_f}
    trange_mode = {task_info['trange']} # 1=Range, 0=Current
    
    do_resume = {str(resume)}
    
    print(f"Loading { hip_file} ...")
    try:
        hou.hipFile.load(hip_file, suppress_save_prompt=True)
    except hou.LoadWarning:
        pass
        
    node = hou.node(node_path)
    if not node:
        print(f"Error: Node { node_path}  not found.")
        sys.exit(1)
        
    # If not range mode, just render current/1 frame (or let's just do frame 1 for simplicity if user didn't check range)
    # Ideally should read $F from file but simpler to treat as frame 1 if unknown.
    if trange_mode == 0:
        # Just render current frame saved in file?
        # Actually hrender default is often frame 1 or current
        frames = [hou.frame()] 
    else:
        # Generate range
        # Use simple loop to handle float/int issues
        frames = []
        curr = start
        while curr <= end:
            frames.append(curr)
            curr += inc
            
    total = len(frames)
    print(f"Starting render for { total}  frames...")
    
    for i, f in enumerate(frames):
        try:
            hou.setFrame(f)
            
            # Resume Check
            if do_resume:
                out_path = get_output_path(node)
                if out_path:
                    # Resolve $F variants just in case eval didn't Catch it (eval usually done)
                    # out_path should be absolute or correct relative
                    if os.path.exists(out_path):
                        print(f"Frame { f}  : Skipping (Exists) -> { out_path} ")
                        continue
                    else:
                        print(f"DEBUG: Frame { f}  Path='{ out_path} ' Exists=False CWD='{ os.getcwd()} '")
                else:
                    print(f"DEBUG: No output path detected for node { node.path()} ")
            
            print(f"Rendering Frame { int(f)}  ({ i+1} /{ total} )...")
            # Render single frame
            # frame_range expects (start, end)
            node.render(frame_range=(f, f), verbose=False)
            
        except Exception as e:
            print(f"Error rendering frame { int(f)} : { e} ")
            # Don't exit, try next frame? or exit? Usually better to fail.
            sys.exit(1)
            
    print("Task Complete.")

if __name__ == "__main__":
    main()
"""
        temp_dir = tempfile.gettempdir()
        script_path = os.path.join(temp_dir, f"render_task_{os.getpid()}.py")
        with open(script_path, "w", encoding='utf-8') as f:
            f.write(script_content)
            
        hip_dir = os.path.dirname(hip_file)
        self.process.setWorkingDirectory(hip_dir)
        
        args = [script_path]
        
        self.log_output.append(f"Custom Script Render Mode")
        self.log_output.append(f"CWD: {hip_dir}")
        self.log_output.append(f"Resume: {'ON' if resume else 'OFF'}")
        
        self.process.start(hython_exe, args)

    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode(errors='ignore')
        if data.strip():
            self.log_output.append(data.strip())
            
            import re
                                                     
            match = re.search(r'\((\d+)/(\d+)\)', data)
            if match:
                current = int(match.group(1))
                total = int(match.group(2))
                percent = int((current / total) * 100)
                self.progress_bar.setValue(percent)
                return
            
            match = re.search(r'\((\d+)\s+of\s+(\d+)\)', data)
            if match:
                current = int(match.group(1))
                total = int(match.group(2))
                percent = int((current / total) * 100)
                self.progress_bar.setValue(percent)
            
    def handle_stderr(self):
        err = self.process.readAllStandardError().data().decode(errors='ignore')
        if err.strip():
             self.log_output.append(f"[ERROR] {err.strip()}")

    def on_task_finished(self):
                             
        temp_dir = tempfile.gettempdir()
        script_path = os.path.join(temp_dir, f"render_task_{ os.getpid()} .py")
        if os.path.exists(script_path):
            try:
                os.remove(script_path)
            except:
                pass
                
        if self.process.exitCode() == 0:
            self.log_output.append("✓ Task Finished")
            self.run_next_task()
        else:
                         
            if self.chk_continue_on_error.isChecked():
                                                   
                if hasattr(self, 'current_task'):
                    self.failed_tasks.append(self.current_task)
                self.log_output.append("❌ Task Failed - Continuing to next task...")
                self.run_next_task()
            else:
                                                           
                self.log_output.append("✕ Task Failed - Queue stopped")

    def stop_render(self):
        self.tasks = []
        self.process.kill()
        self.log_output.append(self.t("msg_manual_stop"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RenderManager()
    window.show()
    sys.exit(app.exec())