# -*- coding:gb18030 -*-
import sys
import os
import re
from collections import Counter
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTextEdit, QCheckBox, QFileDialog, QMessageBox)
from PyQt5.QtGui import QIcon

class BatchRenameTool(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.original_file_names = []  # 保存原始文件名
        self.rename_operations = []  # 保存重命名操作
        self.current_extension = ''  # 扩展名

    def initUI(self):
        layout = QVBoxLayout()

        # 文件夹路径
        folderLayout = QHBoxLayout()
        self.folderLabel = QLabel('文件夹路径:')
        self.folderLineEdit = QLineEdit()
        self.browseButton = QPushButton('浏览...')
        self.browseButton.clicked.connect(self.browseFolder)
        folderLayout.addWidget(self.folderLabel)
        folderLayout.addWidget(self.folderLineEdit)
        folderLayout.addWidget(self.browseButton)
        
        # 原始文件名
        self.originalLabel = QLabel('原始文件名:')
        self.originalTextEdit = QTextEdit()
        self.originalTextEdit.setReadOnly(True)  # 设置为只读

        # 替换后文件名
        self.replaceLabel = QLabel('替换后文件名:')
        self.replaceLineEdit = QLineEdit()  # 改为单行输入框

        # 顺序输入框
        self.sequenceLabel = QLabel('顺序（用逗号分隔）:')
        self.sequenceLineEdit = QLineEdit()
        self.sequenceLabel.hide()
        self.sequenceLineEdit.hide()

        # 选项
        optionsLayout = QHBoxLayout()
        self.includeExtensionCheckBox = QCheckBox('包含扩展名')
        self.includeExtensionCheckBox.stateChanged.connect(self.updateReplaceLineEdit)  # 连接到更新函数
        self.correctOrderCheckBox = QCheckBox('按正确顺序重命名')
        self.removeSpecialCharCheckBox = QCheckBox('去除特殊符号')
        self.correctOrderCheckBox.stateChanged.connect(self.toggleSequenceInput)
        optionsLayout.addWidget(self.includeExtensionCheckBox)
        optionsLayout.addWidget(self.correctOrderCheckBox)
        optionsLayout.addWidget(self.removeSpecialCharCheckBox)

        # 重命名按钮
        self.renameButton = QPushButton('重命名文件')
        self.renameButton.clicked.connect(self.renameFiles)

        # 撤销按钮
        self.undoButton = QPushButton('撤销重命名')
        self.undoButton.clicked.connect(self.undoRename)

        layout.addLayout(folderLayout)
        layout.addWidget(self.originalLabel)
        layout.addWidget(self.originalTextEdit)
        layout.addWidget(self.replaceLabel)
        layout.addWidget(self.replaceLineEdit)  # 使用单行输入框
        layout.addWidget(self.sequenceLabel)
        layout.addWidget(self.sequenceLineEdit)
        layout.addLayout(optionsLayout)
        layout.addWidget(self.renameButton)
        layout.addWidget(self.undoButton)

        self.setLayout(layout)
        self.setWindowTitle('文件批量重命名')

    def browseFolder(self):
        folder = QFileDialog.getExistingDirectory(self, '选择文件夹')
        if folder:
            self.folderLineEdit.setText(folder)
            self.displayOriginalFileNames(folder)
            self.updateReplaceLineEdit()

    def displayOriginalFileNames(self, folderPath):
        try:
            files = os.listdir(folderPath)
            self.original_file_names = [file for file in files]
            file_count = Counter([os.path.splitext(file)[0] for file in files])
            most_common_files = file_count.most_common()

            self.originalTextEdit.clear()
            for file_name, count in most_common_files:
                self.originalTextEdit.append(file_name)

            if files:
                self.current_extension = os.path.splitext(files[0])[1]
            else:
                self.current_extension = ''
        except Exception as e:
            self.showMessage("错误", f"无法读取文件夹中的文件: {e}")

    def showMessage(self, title, message):
        msgBox = QMessageBox()
        msgBox.setWindowTitle(title)
        msgBox.setText(message)
        msgBox.exec_()

    def toggleSequenceInput(self, state):
        if state == 2:  
            self.sequenceLabel.show()
            self.sequenceLineEdit.show()
        else:
            self.sequenceLabel.hide()
            self.sequenceLineEdit.hide()

    def updateReplaceLineEdit(self):
        if self.includeExtensionCheckBox.isChecked():
            current_text = self.replaceLineEdit.text()
            if not current_text.endswith(self.current_extension):
                self.replaceLineEdit.setText(current_text + self.current_extension)
        else:
            current_text = self.replaceLineEdit.text()
            if current_text.endswith(self.current_extension):
                self.replaceLineEdit.setText(current_text[:-len(self.current_extension)])

    def renameFiles(self):
        folderPath = self.folderLineEdit.text()
        newNameFormat = self.replaceLineEdit.text()
        includeExtension = self.includeExtensionCheckBox.isChecked()
        correctOrder = self.correctOrderCheckBox.isChecked()
        removeSpecialChars = self.removeSpecialCharCheckBox.isChecked()
        sequence = self.sequenceLineEdit.text()

        if not newNameFormat:
            self.showMessage("错误", "请提供替换后的文件名格式")
            return

        files = os.listdir(folderPath)

        if correctOrder:
            if not sequence:
                self.showMessage("错误", "请输入顺序（用逗号隔开）")
                return

            try:
                sequence = [int(num) for num in sequence.split(',')]
            except ValueError:
                self.showMessage("错误", "顺序格式错误，请确保输入的都是数字并用逗号分隔")
                return

            if len(files) != len(sequence):
                self.showMessage("错误", "文件数量与提供的顺序数量不一致")
                return

            # 根据顺序创建映射
            mapping = {orig: new for new, orig in enumerate(sequence, start=1)}

            self.rename_operations = []
            for orig_index, file in enumerate(files):
                new_index = mapping.get(orig_index + 1, None)
                if new_index is not None:
                    file_name, ext = os.path.splitext(file)

                    # 生成新的文件名
                    new_file_name = newNameFormat.replace("%n", str(new_index)).replace("%f", file_name)
                    if includeExtension:
                        new_file_name += ext
                    else:
                        # 如果不包含扩展名，则仅替换文件名部分，并保留扩展名
                        new_file_name = os.path.splitext(new_file_name)[0]

                    if removeSpecialChars:
                        new_file_name = re.sub(r'[^\w\s]', '', new_file_name)

                    # 确保新文件名唯一
                    new_file_name = self.ensureUniqueName(folderPath, new_file_name, ext, includeExtension)
                    
                    self.rename_operations.append((file, new_file_name + (ext if not includeExtension else '')))
        else:
            self.rename_operations = []
            for index, file in enumerate(files):
                file_name, ext = os.path.splitext(file)

                # 生成新的文件名
                new_file_name = newNameFormat.replace("%n", str(index + 1)).replace("%f", file_name)
                if includeExtension:
                    new_file_name += ext
                else:
                    # 如果不包含扩展名，则仅替换文件名部分，并保留扩展名
                    new_file_name = os.path.splitext(new_file_name)[0]

                if removeSpecialChars:
                    new_file_name = re.sub(r'[^\w\s]', '', new_file_name)

                # 确保新文件名唯一
                new_file_name = self.ensureUniqueName(folderPath, new_file_name, ext, includeExtension)

                self.rename_operations.append((file, new_file_name + (ext if not includeExtension else '')))

        # 执行重命名
        for old_name, new_name in self.rename_operations:
            old_file_path = os.path.join(folderPath, old_name)
            new_file_path = os.path.join(folderPath, new_name)
            os.rename(old_file_path, new_file_path)

        # 重命名完成后，重新读取文件夹并更新显示
        self.displayOriginalFileNames(folderPath)
        self.showMessage("完成", "文件重命名完成")

    def ensureUniqueName(self, folderPath, newFileName, extension, includeExtension):
        counter = 1
        uniqueName = newFileName
        if includeExtension:
            while os.path.exists(os.path.join(folderPath, uniqueName)):
                uniqueName = f"{newFileName} ({counter}){extension}"
                counter += 1
        else:
            while os.path.exists(os.path.join(folderPath, uniqueName + extension)):
                uniqueName = f"{newFileName} ({counter})"
                counter += 1
        return uniqueName

    def undoRename(self):
        folderPath = self.folderLineEdit.text()

        for old_name, new_name in reversed(self.rename_operations):
            old_file_path = os.path.join(folderPath, old_name)
            new_file_path = os.path.join(folderPath, new_name)
            if os.path.exists(new_file_path):
                os.rename(new_file_path, old_file_path)

        # 撤销完成后，重新读取文件夹并更新显示
        self.displayOriginalFileNames(folderPath)
        self.showMessage("完成", "撤销重命名完成")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    ex = BatchRenameTool()
    ex.show()
    sys.exit(app.exec_())
