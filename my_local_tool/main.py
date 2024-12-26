import sys
import platform
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QFileDialog, QLabel, QSpinBox, 
                            QHBoxLayout, QProgressBar, QScrollArea, QCheckBox,
                            QGraphicsDropShadowEffect, QMessageBox, QProgressDialog)
from PyQt6.QtCore import Qt, QSize, QMimeData, QPoint, QPropertyAnimation
from PyQt6.QtGui import QPixmap, QDrag, QImage, QColor
import cv2
import os
import re
import numpy as np  # 添加 numpy 导入

def natural_sort_key(s):
    """用于自然排序的键函数"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        # 如果是打包后的应用
        if sys.platform == 'win32':
            return os.path.join(sys._MEIPASS, 'ffmpeg.exe')
        else:
            # macOS 上优先使用打包的 ffmpeg
            bundled_ffmpeg = os.path.join(sys._MEIPASS, 'ffmpeg')
            if os.path.exists(bundled_ffmpeg):
                # 确保有执行权限
                os.chmod(bundled_ffmpeg, 0o755)
                return bundled_ffmpeg
            
            # 如果打包的 ffmpeg 不存在，尝试系统路径
            possible_paths = [
                '/usr/local/bin/ffmpeg',
                '/opt/homebrew/bin/ffmpeg',
                '/usr/bin/ffmpeg',
                'ffmpeg'
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            raise Exception("找不到 ffmpeg")
    return 'ffmpeg'  # 开发环境使用系统安装的 ffmpeg

def show_install_progress(process, progress_dialog):
    """显示安装进度"""
    while process.poll() is None:
        output = process.stdout.readline()
        if output:
            # 更新进度对话框的文本
            progress_dialog.setLabelText(output.strip())
        QApplication.processEvents()  # 保持界面响应

def check_ffmpeg():
    """检查 ffmpeg 是否可用"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_bundled_ffmpeg():
    """安装打包的 ffmpeg"""
    try:
        if getattr(sys, 'frozen', False):
            bundled_ffmpeg = os.path.join(sys._MEIPASS, 'ffmpeg' if sys.platform != 'win32' else 'ffmpeg.exe')
            if os.path.exists(bundled_ffmpeg):
                if sys.platform != 'win32':
                    os.chmod(bundled_ffmpeg, 0o755)
                try:
                    subprocess.run([bundled_ffmpeg, '-version'], capture_output=True, check=True)
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass
        return False
    except Exception:
        return False

def show_install_instructions():
    """显示安装指导"""
    system = platform.system()
    if system == 'Darwin':  # macOS
        instructions = (
            "请在终端执行以下命令安装 FFmpeg：\n\n"
            "1. 安装 Homebrew（如果未安装）：\n"
            "/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"\n\n"
            "2. 安装 FFmpeg：\n"
            "brew install ffmpeg"
        )
    elif system == 'Windows':
        instructions = (
            "请按以下步骤安装 FFmpeg：\n\n"
            "1. 访问 https://ffmpeg.org/download.html\n"
            "2. 下载 Windows 版本\n"
            "3. 解压并将 ffmpeg.exe 添加到系统环境变量"
        )
    else:  # Linux
        instructions = (
            "请使用包管理器安装 FFmpeg：\n\n"
            "Ubuntu/Debian:\n"
            "sudo apt update && sudo apt install ffmpeg\n\n"
            "CentOS/RHEL:\n"
            "sudo yum install ffmpeg"
        )
    
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setWindowTitle("安装 FFmpeg")
    msg.setText("需要安装 FFmpeg 才能继续。")
    msg.setDetailedText(instructions)
    msg.setStandardButtons(
        QMessageBox.StandardButton.Retry |  # 重试按钮
        QMessageBox.StandardButton.Cancel   # 取消按钮
    )
    return msg.exec()

def check_and_install_ffmpeg():
    """检查并安装 ffmpeg"""
    # 1. 检查系统 ffmpeg
    if check_ffmpeg():
        return True
        
    # 2. 尝试使用打包的 ffmpeg
    if install_bundled_ffmpeg():
        return True
        
    # 3. 显示安装指导并等待用户操作
    while True:
        response = show_install_instructions()
        
        if response == QMessageBox.StandardButton.Retry:
            # 用户点击重试，检查是否已安装
            if check_ffmpeg():
                QMessageBox.information(None, "成功", "FFmpeg 已成功安装！")
                return True
        else:
            # 用户点击取消
            return False

class DraggableImageLabel(QWidget):
    def __init__(self, pixmap, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.is_hovering = False  # 添加悬停状态跟踪
        self.original_pos = None  # 记录原始位置
        self.anim = None  # 动画对象
        
        # 创建垂直布局
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建图片标签
        self.image_label = QLabel()
        self.image_label.setPixmap(pixmap)
        self.image_label.setMinimumSize(100, 150)
        self.image_label.setMaximumSize(150, 150)
        self.image_label.setScaledContents(True)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px solid #ccc;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        # 创建文件名标签
        self.name_label = QLabel(os.path.basename(file_path))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setMaximumWidth(150)
        self.name_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 10px;
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 3px;
                padding: 2px;
            }
        """)
        self.name_label.hide()  # 默认隐藏文件名
        
        # 添加到布局
        layout.addWidget(self.image_label)
        layout.addWidget(self.name_label)
        
        # 设置阴影效果
        self.setGraphicsEffect(None)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.file_path)
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.MoveAction)
            
    def enterEvent(self, event):
        if self.anim and self.anim.state() == QPropertyAnimation.State.Running:
            self.anim.stop()
        
        if not self.is_hovering:
            self.is_hovering = True
            self.original_pos = self.pos()
            
            # 创建动画效果
            self.anim = QPropertyAnimation(self, b"pos")
            self.anim.setDuration(150)  # 缩短动画时间
            self.anim.setStartValue(self.pos())
            self.anim.setEndValue(QPoint(self.pos().x(), self.pos().y() - 20))
            self.anim.start()
            
            # 放大效果
            self.image_label.setMaximumSize(200, 200)
            
            # 显示文件名
            self.name_label.show()
            
            # 添加阴影效果
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15)
            shadow.setOffset(0, 0)
            shadow.setColor(QColor(0, 0, 0, 100))
            self.setGraphicsEffect(shadow)
        
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        if self.anim and self.anim.state() == QPropertyAnimation.State.Running:
            self.anim.stop()
            
        if self.is_hovering and self.original_pos:
            self.is_hovering = False
            
            # 恢复位置
            self.anim = QPropertyAnimation(self, b"pos")
            self.anim.setDuration(150)  # 缩短动画时间
            self.anim.setStartValue(self.pos())
            self.anim.setEndValue(self.original_pos)
            self.anim.finished.connect(self.on_animation_finished)
            self.anim.start()
            
            # 恢复大小
            self.image_label.setMaximumSize(150, 150)
            
            # 隐藏文件名
            self.name_label.hide()
            
            # 移除阴影效果
            self.setGraphicsEffect(None)
        
        super().leaveEvent(event)
        
    def on_animation_finished(self):
        # 动画完成后理
        if not self.is_hovering:
            self.original_pos = None
            self.anim = None

class ImagePreviewArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.image_labels = []
        
        # 设置固定高度
        self.setFixedHeight(200)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateImageLayout()
        
    def updateImageLayout(self):
        if not self.image_labels:
            return
            
        # 获取可用宽度
        available_width = self.width()
        
        # 计算每张图片的宽度（基于高度等比例缩放）
        image_height = 150  # 固定高度
        image_width = int(image_height * 4/3)  # 假设4:3比例，或者可以根据实际图片调整
        
        # 计算露出的宽度（最后一张完整显示）
        if len(self.image_labels) == 1:
            visible_width = image_width  # 如果只有一张图片，显示整宽度
        else:
            remaining_width = available_width - image_width  # 减去最后一张图片的宽度
            visible_width = remaining_width / (len(self.image_labels) - 1)  # 平均分配给其他图片
            visible_width = min(visible_width, image_width - 30)  # 确保至少30像素的重叠
            
        # 计算总宽度和每张图片的位置
        for i, label in enumerate(self.image_labels):
            if i == len(self.image_labels) - 1:  # 最后一张图片
                x_pos = available_width - image_width
            else:
                x_pos = int(i * visible_width)  # 转换为整数
            
            # 设置图片位置和大小
            label.setGeometry(int(x_pos), 0, image_width, 200)  # 确保所有参数都是整数
            
            # 设置Z顺序，确保正确的叠放顺序（后面的图片在上层）
            label.raise_()
            
    def updateLayout(self):
        # 清除现有布局
        for i in reversed(range(self.layout.count())): 
            self.layout.itemAt(i).widget().setParent(None)
        
        # 重新添加标签
        for label in self.image_labels:
            self.layout.addWidget(label)
            
        # 更新图片布局
        self.updateImageLayout()
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
            
    def dropEvent(self, event):
        file_path = event.mimeData().text()
        source_label = event.source()
        drop_position = event.position().toPoint()
        
        # 找到目标位置
        target_idx = -1
        for i, label in enumerate(self.image_labels):
            if label.geometry().contains(drop_position):
                target_idx = i
                break
                
        if target_idx != -1:
            # 获取源标签的索引
            source_idx = self.image_labels.index(source_label)
            # 重新排序
            self.image_labels.insert(target_idx, self.image_labels.pop(source_idx))
            # 更新布局
            self.updateLayout()
            
    def addImage(self, file_path):
        # 读取图片创建缩略图
        image = cv2.imread(file_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w = image.shape[:2]
        
        # 计算缩放比例，保持原始高比
        target_height = 150
        ratio = target_height / h
        new_width = int(w * ratio)
        
        # 调整图片大小
        image = cv2.resize(image, (new_width, target_height))
        
        # 转为QPixmap
        height, width = image.shape[:2]
        bytes_per_line = 3 * width
        qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        
        # 创建可拖拽的标签
        label_widget = DraggableImageLabel(pixmap, file_path)
        self.image_labels.append(label_widget)
        self.layout.addWidget(label_widget)
        
        # 更新布局
        self.updateImageLayout()
        
    def getImageFiles(self):
        return [label.file_path for label in self.image_labels]

class ImageToVideoConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片转视频工具")
        self.setMinimumSize(800, 600)
        
        # 检查并安装 ffmpeg
        check_and_install_ffmpeg()
        
        # 初始化变量
        self.image_files = []
        self.audio_file = None
        self.aspect_ratio = 16/9  # 默认宽高比
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建控件
        self.create_widgets(layout)
        
    def create_widgets(self, layout):
        # 选择图片按钮
        self.select_images_btn = QPushButton("选择图片")
        self.select_images_btn.clicked.connect(self.select_images)
        layout.addWidget(self.select_images_btn)
        
        # 创建图片预览区域的容器
        preview_container = QWidget()
        preview_container.setMinimumHeight(200)
        preview_container.setMaximumHeight(200)
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建图片预览区域
        self.preview_area = ImagePreviewArea()
        preview_layout.addWidget(self.preview_area)
        layout.addWidget(preview_container)
        
        # 显示已选择图片数量
        self.images_label = QLabel("未选择图片")
        layout.addWidget(self.images_label)
        
        # 选择音频按钮
        self.select_audio_btn = QPushButton("选择背景音乐（可选）")
        self.select_audio_btn.clicked.connect(self.select_audio)
        layout.addWidget(self.select_audio_btn)
        
        # 显示已选择音��
        self.audio_label = QLabel("未选择音频")
        layout.addWidget(self.audio_label)
        
        # 帧率设置
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("帧率:"))
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 60)
        self.fps_spinbox.setValue(30)
        fps_layout.addWidget(self.fps_spinbox)
        layout.addLayout(fps_layout)
        
        # 分辨率设置
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel("分辨率:"))
        
        # 创建宽度输入框
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(1, 7680)
        self.width_spinbox.setValue(1920)
        self.width_spinbox.valueChanged.connect(self.on_width_changed)
        resolution_layout.addWidget(self.width_spinbox)
        
        resolution_layout.addWidget(QLabel("x"))
        
        # 创建高度输入框
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(1, 4320)
        self.height_spinbox.setValue(1080)
        self.height_spinbox.valueChanged.connect(self.on_height_changed)
        resolution_layout.addWidget(self.height_spinbox)
        
        # 添加固定宽高比复选框
        self.keep_ratio_checkbox = QCheckBox("固定宽高比")
        self.keep_ratio_checkbox.setChecked(False)
        self.keep_ratio_checkbox.stateChanged.connect(self.on_keep_ratio_changed)
        resolution_layout.addWidget(self.keep_ratio_checkbox)
        
        layout.addLayout(resolution_layout)
        
        # 生成视频按钮
        self.generate_btn = QPushButton("生成视频")
        self.generate_btn.clicked.connect(self.generate_video)
        layout.addWidget(self.generate_btn)
        
        # 进度条
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
    def select_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        if files:
            self.preview_area.image_labels.clear()
            
            # 获取所有图片中最大尺寸
            max_width = 0
            max_height = 0
            for file in files:
                img = cv2.imread(file)
                if img is not None:
                    h, w = img.shape[:2]
                    max_width = max(max_width, w)
                    max_height = max(max_height, h)
            
            # 更新分辨率设置
            self.width_spinbox.blockSignals(True)
            self.height_spinbox.blockSignals(True)
            self.width_spinbox.setValue(max_width)
            self.height_spinbox.setValue(max_height)
            self.height_spinbox.blockSignals(False)
            self.width_spinbox.blockSignals(False)
            
            # 使用自然排序
            sorted_files = sorted(files, key=natural_sort_key)
            for file in sorted_files:
                self.preview_area.addImage(file)
            self.images_label.setText(f"已选择 {len(files)} 张图片")
            
    def select_audio(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "选择音频文件",
            "",
            "音频文件 (*.mp3 *.wav)"
        )
        if file:
            self.audio_file = file
            self.audio_label.setText(f"已选择: {os.path.basename(file)}")
            
    def generate_video(self):
        try:
            # 在生成视频前检查 ffmpeg
            if self.audio_file:  # 只有在需要合并音频时才需要 ffmpeg
                if not check_and_install_ffmpeg():
                    QMessageBox.warning(self, "警告", 
                        "未安装 FFmpeg，将生成无音频的视频。\n"
                        "如需添加音频，请安装 FFmpeg 后重试。")
                    self.audio_file = None  # 清除音��文件选择
            
            # 获取当前排序后的图片文件列表
            self.image_files = self.preview_area.getImageFiles()
            
            if not self.image_files:
                self.images_label.setText("请先选择图片！")
                return
            
            output_file, _ = QFileDialog.getSaveFileName(
                self,
                "保存视频",
                "",
                "视频文件 (*.mp4)"
            )
            
            if output_file:
                self.progress_bar.setValue(0)
                
                # 使用用户设置的分辨率
                target_width = self.width_spinbox.value()
                target_height = self.height_spinbox.value()
                fps = self.fps_spinbox.value()
                
                # 创建临时视频文件
                temp_video = output_file + "_temp.mp4"
                
                try:
                    # 创建视频写入器
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    out = cv2.VideoWriter(temp_video, fourcc, fps, (target_width, target_height))
                    
                    if not out.isOpened():
                        raise Exception("无法创建视频文件")
                    
                    # 写入帧
                    total_frames = len(self.image_files)
                    for i, image_file in enumerate(self.image_files):
                        img = cv2.imread(image_file)
                        if img is None:
                            raise Exception(f"无法读取图片: {image_file}")
                        
                        # 调整图片大小，保持宽高比
                        h, w = img.shape[:2]
                        ratio = min(target_width/w, target_height/h)
                        new_w = int(w * ratio)
                        new_h = int(h * ratio)
                        
                        # 调整图片大小
                        resized = cv2.resize(img, (new_w, new_h))
                        
                        # 创建空白背景
                        canvas = np.zeros((target_height, target_width, 3), dtype=np.uint8)
                        
                        # 将调整后的图片放在中间
                        y_offset = (target_height - new_h) // 2
                        x_offset = (target_width - new_w) // 2
                        canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
                        
                        out.write(canvas)
                        
                        # 更新进度条
                        progress = int((i + 1) / total_frames * 100)
                        self.progress_bar.setValue(progress)
                        
                        # 处理 Qt 事件，保持界面响应
                        QApplication.processEvents()
                    
                    out.release()
                    
                    # 如果选择了音频文件，使用 ffmpeg 合并视频和音频
                    if self.audio_file:
                        cmd = [
                            get_ffmpeg_path(),
                            '-i', temp_video,
                            '-i', self.audio_file,
                            '-c:v', 'copy',
                            '-c:a', 'aac',
                            '-shortest',
                            output_file
                        ]
                        
                        # 使用 subprocess.run 的完整参数
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        
                        if result.returncode != 0:
                            raise Exception(f"FFmpeg 错误: {result.stderr}")
                        
                        os.remove(temp_video)  # 删除临时文件
                    else:
                        os.rename(temp_video, output_file)
                    
                    self.progress_bar.setValue(100)
                    self.images_label.setText("视频生成完成！")
                    
                except Exception as e:
                    # 清理临时文件
                    if os.path.exists(temp_video):
                        try:
                            os.remove(temp_video)
                        except:
                            pass
                    raise e  # 重新抛出异常
                
        except Exception as e:
            # 显示错误消息
            QMessageBox.critical(self, "错误", f"生成视频时出错：\n{str(e)}")
            self.progress_bar.setValue(0)
            self.images_label.setText("生成失败")

    def on_keep_ratio_changed(self, state):
        if state == Qt.CheckState.Checked.value:
            # 勾选时，保存当前的宽高比
            self.aspect_ratio = self.width_spinbox.value() / self.height_spinbox.value()

    def on_width_changed(self, new_width):
        if self.keep_ratio_checkbox.isChecked():
            # 使用保存的宽高比
            new_height = int(new_width / self.aspect_ratio)
            # 确保新高度在有效范围内
            new_height = max(1, min(new_height, 4320))
            # 更新高度，但不触发高度变化事件
            self.height_spinbox.blockSignals(True)
            self.height_spinbox.setValue(new_height)
            self.height_spinbox.blockSignals(False)

    def on_height_changed(self, new_height):
        if self.keep_ratio_checkbox.isChecked():
            # 使用保存的宽高比
            new_width = int(new_height * self.aspect_ratio)
            # 确保新宽度在有效范围内
            new_width = max(1, min(new_width, 7680))
            # 更新宽度，但不触发宽度变化事件
            self.width_spinbox.blockSignals(True)
            self.width_spinbox.setValue(new_width)
            self.width_spinbox.blockSignals(False)

def main():
    app = QApplication(sys.argv)
    window = ImageToVideoConverter()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 