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
        self.original_file_names = []  # ����ԭʼ�ļ���
        self.rename_operations = []  # ��������������
        self.current_extension = ''  # ��չ��

    def initUI(self):
        layout = QVBoxLayout()

        # �ļ���·��
        folderLayout = QHBoxLayout()
        self.folderLabel = QLabel('�ļ���·��:')
        self.folderLineEdit = QLineEdit()
        self.browseButton = QPushButton('���...')
        self.browseButton.clicked.connect(self.browseFolder)
        folderLayout.addWidget(self.folderLabel)
        folderLayout.addWidget(self.folderLineEdit)
        folderLayout.addWidget(self.browseButton)
        
        # ԭʼ�ļ���
        self.originalLabel = QLabel('ԭʼ�ļ���:')
        self.originalTextEdit = QTextEdit()
        self.originalTextEdit.setReadOnly(True)  # ����Ϊֻ��

        # �滻���ļ���
        self.replaceLabel = QLabel('�滻���ļ���:')
        self.replaceLineEdit = QLineEdit()  # ��Ϊ���������

        # ˳�������
        self.sequenceLabel = QLabel('˳���ö��ŷָ���:')
        self.sequenceLineEdit = QLineEdit()
        self.sequenceLabel.hide()
        self.sequenceLineEdit.hide()

        # ѡ��
        optionsLayout = QHBoxLayout()
        self.includeExtensionCheckBox = QCheckBox('������չ��')
        self.includeExtensionCheckBox.stateChanged.connect(self.updateReplaceLineEdit)  # ���ӵ����º���
        self.correctOrderCheckBox = QCheckBox('����ȷ˳��������')
        self.removeSpecialCharCheckBox = QCheckBox('ȥ���������')
        self.correctOrderCheckBox.stateChanged.connect(self.toggleSequenceInput)
        optionsLayout.addWidget(self.includeExtensionCheckBox)
        optionsLayout.addWidget(self.correctOrderCheckBox)
        optionsLayout.addWidget(self.removeSpecialCharCheckBox)

        # ��������ť
        self.renameButton = QPushButton('�������ļ�')
        self.renameButton.clicked.connect(self.renameFiles)

        # ������ť
        self.undoButton = QPushButton('����������')
        self.undoButton.clicked.connect(self.undoRename)

        layout.addLayout(folderLayout)
        layout.addWidget(self.originalLabel)
        layout.addWidget(self.originalTextEdit)
        layout.addWidget(self.replaceLabel)
        layout.addWidget(self.replaceLineEdit)  # ʹ�õ��������
        layout.addWidget(self.sequenceLabel)
        layout.addWidget(self.sequenceLineEdit)
        layout.addLayout(optionsLayout)
        layout.addWidget(self.renameButton)
        layout.addWidget(self.undoButton)

        self.setLayout(layout)
        self.setWindowTitle('�ļ�����������')

    def browseFolder(self):
        folder = QFileDialog.getExistingDirectory(self, 'ѡ���ļ���')
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
            self.showMessage("����", f"�޷���ȡ�ļ����е��ļ�: {e}")

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
            self.showMessage("����", "���ṩ�滻����ļ�����ʽ")
            return

        files = os.listdir(folderPath)

        if correctOrder:
            if not sequence:
                self.showMessage("����", "������˳���ö��Ÿ�����")
                return

            try:
                sequence = [int(num) for num in sequence.split(',')]
            except ValueError:
                self.showMessage("����", "˳���ʽ������ȷ������Ķ������ֲ��ö��ŷָ�")
                return

            if len(files) != len(sequence):
                self.showMessage("����", "�ļ��������ṩ��˳��������һ��")
                return

            # ����˳�򴴽�ӳ��
            mapping = {orig: new for new, orig in enumerate(sequence, start=1)}

            self.rename_operations = []
            for orig_index, file in enumerate(files):
                new_index = mapping.get(orig_index + 1, None)
                if new_index is not None:
                    file_name, ext = os.path.splitext(file)

                    # �����µ��ļ���
                    new_file_name = newNameFormat.replace("%n", str(new_index)).replace("%f", file_name)
                    if includeExtension:
                        new_file_name += ext
                    else:
                        # �����������չ��������滻�ļ������֣���������չ��
                        new_file_name = os.path.splitext(new_file_name)[0]

                    if removeSpecialChars:
                        new_file_name = re.sub(r'[^\w\s]', '', new_file_name)

                    # ȷ�����ļ���Ψһ
                    new_file_name = self.ensureUniqueName(folderPath, new_file_name, ext, includeExtension)
                    
                    self.rename_operations.append((file, new_file_name + (ext if not includeExtension else '')))
        else:
            self.rename_operations = []
            for index, file in enumerate(files):
                file_name, ext = os.path.splitext(file)

                # �����µ��ļ���
                new_file_name = newNameFormat.replace("%n", str(index + 1)).replace("%f", file_name)
                if includeExtension:
                    new_file_name += ext
                else:
                    # �����������չ��������滻�ļ������֣���������չ��
                    new_file_name = os.path.splitext(new_file_name)[0]

                if removeSpecialChars:
                    new_file_name = re.sub(r'[^\w\s]', '', new_file_name)

                # ȷ�����ļ���Ψһ
                new_file_name = self.ensureUniqueName(folderPath, new_file_name, ext, includeExtension)

                self.rename_operations.append((file, new_file_name + (ext if not includeExtension else '')))

        # ִ��������
        for old_name, new_name in self.rename_operations:
            old_file_path = os.path.join(folderPath, old_name)
            new_file_path = os.path.join(folderPath, new_name)
            os.rename(old_file_path, new_file_path)

        # ��������ɺ����¶�ȡ�ļ��в�������ʾ
        self.displayOriginalFileNames(folderPath)
        self.showMessage("���", "�ļ����������")

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

        # ������ɺ����¶�ȡ�ļ��в�������ʾ
        self.displayOriginalFileNames(folderPath)
        self.showMessage("���", "�������������")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    ex = BatchRenameTool()
    ex.show()
    sys.exit(app.exec_())
