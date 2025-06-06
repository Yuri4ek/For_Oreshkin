import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, \
    QWidget, QToolBar, QAction, QDialog, QFormLayout, QLineEdit, QTextEdit, QPushButton, QDateEdit, \
    QMessageBox, QFileDialog
from PyQt5.QtCore import QDate, Qt, QTimer
import pandas as pd
import requests

# URL Flask-сервера (замените на актуальный домен/IP и порт при хостинге)
FLASK_URL = "http://192.168.1.103:5000"  # При хостинге: "https://your-domain.com"

class RepairDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Ремонт")
        self.layout = QFormLayout(self)
        self.device_type = QLineEdit(self)
        self.issue_description = QTextEdit(self)
        self.issue_description.setFixedHeight(100)
        self.client_name = QLineEdit(self)
        self.repairer_name = QLineEdit(self)
        self.request_date = QDateEdit(self)
        self.request_date.setCalendarPopup(True)
        self.request_date.setDate(QDate.currentDate())
        self.layout.addRow("Тип устройства:", self.device_type)
        self.layout.addRow("Сообщение о поломке:", self.issue_description)
        self.layout.addRow("Человек (ФИО):", self.client_name)
        self.layout.addRow("Ремонтник (ФИО):", self.repairer_name)
        self.layout.addRow("Дата запроса:", self.request_date)
        self.save_button = QPushButton("Сохранить", self)
        self.save_button.clicked.connect(self.accept)
        self.layout.addWidget(self.save_button)
        if data:
            self.device_type.setText(data[0])
            self.issue_description.setText(data[1])
            self.client_name.setText(data[2])
            self.repairer_name.setText(data[3])
            self.request_date.setDate(QDate.fromString(data[4], "yyyy-MM-dd"))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Учет ремонтов")
        self.resize(1200, 800)
        self.table = QTableWidget(self)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Тип устройства", "Сообщение о поломке", "Человек (ФИО)", "Ремонтник (ФИО)",
             "Дата запроса", "Действия"])
        self.table.setColumnHidden(0, True)
        self.table.cellDoubleClicked.connect(self.edit_record)
        self.table.cellClicked.connect(self.show_issue_description)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 300)
        self.table.setColumnWidth(3, 200)
        self.table.setColumnWidth(4, 200)
        self.table.setColumnWidth(5, 150)
        self.table.setColumnWidth(6, 100)
        self.setCentralWidget(self.table)

        self.toolbar = QToolBar("Действия")
        self.addToolBar(self.toolbar)
        self.load_action = QAction("Загрузить", self)
        self.load_action.triggered.connect(self.load_excel_file)
        self.toolbar.addAction(self.load_action)
        self.save_action = QAction("Выгрузить", self)
        self.save_action.triggered.connect(self.save_data)
        self.toolbar.addAction(self.save_action)
        self.add_action = QAction("Добавить запись", self)
        self.add_action.triggered.connect(self.add_record)
        self.toolbar.addAction(self.add_action)
        self.delete_all_action = QAction("Удалить все", self)
        self.delete_all_action.triggered.connect(self.delete_all_records)
        self.toolbar.addAction(self.delete_all_action)
        self.view_excel_action = QAction("Просмотреть Excel", self)
        self.view_excel_action.triggered.connect(self.view_excel_file)
        self.toolbar.addAction(self.view_excel_action)

        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data)
        self.timer.start(5000)  # Обновление каждые 5 секунд
        self.load_data()

    def load_data(self):
        try:
            response = requests.get(f"{FLASK_URL}/get_repairs", timeout=5)
            if response.status_code == 200:
                rows = response.json()
                self.table.setRowCount(len(rows))
                for i, row in enumerate(rows):
                    self.table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
                    self.table.setItem(i, 1, QTableWidgetItem(row['device_type']))
                    self.table.setItem(i, 2, QTableWidgetItem(row['issue_description']))
                    self.table.setItem(i, 3, QTableWidgetItem(row['client_name']))
                    self.table.setItem(i, 4, QTableWidgetItem(row['repairer_name']))
                    self.table.setItem(i, 5, QTableWidgetItem(row['request_date']))
                    delete_button = QPushButton("Удалить")
                    delete_button.clicked.connect(lambda checked, r=i, id=row['id']: self.delete_record(r, id))
                    self.table.setCellWidget(i, 6, delete_button)
            else:
                QMessageBox.critical(self, "Ошибка", f"Ошибка сервера: {response.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")

    def save_data(self):
        try:
            data = [[self.table.item(i, j).text() for j in range(1, 6)]
                    for i in range(self.table.rowCount())]
            df = pd.DataFrame(data, columns=["Тип устройства", "Сообщение о поломке",
                                             "Человек (ФИО)", "Ремонтник (ФИО)", "Дата запроса"])
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "",
                                                       "Excel files (*.xlsx)")
            if file_path:
                df.to_excel(file_path, index=False)
                QMessageBox.information(self, "Успех", f"Данные выгружены в {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def add_record(self):
        dialog = RepairDialog(self)
        if dialog.exec_():
            data = {
                'type': dialog.device_type.text(),
                'description': dialog.issue_description.toPlainText(),
                'user': dialog.client_name.text(),
                'repairer_name': dialog.repairer_name.text(),
                'time': dialog.request_date.date().toString("yyyy-MM-dd")
            }
            try:
                response = requests.post(f"{FLASK_URL}/receive", json=data, timeout=5)
                if response.status_code == 200:
                    QMessageBox.information(self, "Успех", "Запись добавлена")
                    self.load_data()
                else:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка сервера: {response.status_code}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись: {str(e)}")

    def edit_record(self, row, column):
        if column == 6:
            return
        id_item = self.table.item(row, 0)
        if id_item:
            record_id = int(id_item.text())
            data = [self.table.item(row, i).text() for i in range(1, 6)]
            dialog = RepairDialog(self, data)
            if dialog.exec_():
                new_data = {
                    'type': dialog.device_type.text(),
                    'description': dialog.issue_description.toPlainText(),
                    'user': dialog.client_name.text(),
                    'repairer_name': dialog.repairer_name.text(),
                    'time': dialog.request_date.date().toString("yyyy-MM-dd")
                }
                try:
                    # Удаляем старую запись через Flask
                    response = requests.delete(f"{FLASK_URL}/delete_repair/{record_id}", timeout=5)
                    if response.status_code != 200:
                        raise Exception(f"Ошибка удаления: {response.status_code}")
                    # Добавляем обновленную запись
                    response = requests.post(f"{FLASK_URL}/receive", json=new_data, timeout=5)
                    if response.status_code == 200:
                        QMessageBox.information(self, "Успех", "Запись обновлена")
                        self.load_data()
                    else:
                        raise Exception(f"Ошибка сервера: {response.status_code}")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось обновить запись: {str(e)}")

    def show_issue_description(self, row, column):
        if column == 2:
            issue = self.table.item(row, 2).text()
            QMessageBox.information(self, "Сообщение о поломке", issue)

    def delete_record(self, row, record_id):
        reply = QMessageBox.question(self, "Подтверждение",
                                     f"Вы уверены, что хотите удалить запись ID {record_id}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                response = requests.delete(f"{FLASK_URL}/delete_repair/{record_id}", timeout=5)
                if response.status_code == 200:
                    QMessageBox.information(self, "Успех", "Запись удалена")
                    self.load_data()
                else:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка сервера: {response.status_code}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить запись: {str(e)}")

    def delete_all_records(self):
        reply = QMessageBox.question(self, "Подтверждение",
                                     "Вы уверены, что хотите удалить все записи?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                response = requests.delete(f"{FLASK_URL}/delete_all_repairs", timeout=5)
                if response.status_code == 200:
                    QMessageBox.information(self, "Успех", "Все записи удалены")
                    self.load_data()
                else:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка сервера: {response.status_code}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить записи: {str(e)}")

    def view_excel_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать файл Excel", "",
                                                   "Excel files (*.xlsx *.xls)")
        if file_path:
            try:
                df = pd.read_excel(file_path)
                dialog = QDialog(self)
                dialog.setWindowTitle("Просмотр Excel")
                layout = QVBoxLayout(dialog)
                table = QTableWidget(dialog)
                table.setRowCount(df.shape[0])
                table.setColumnCount(df.shape[1])
                table.setHorizontalHeaderLabels(df.columns)
                for i in range(df.shape[0]):
                    for j in range(df.shape[1]):
                        table.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))
                layout.addWidget(table)
                dialog.setLayout(layout)
                dialog.resize(800, 600)
                dialog.exec_()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def load_excel_file(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать файл Excel", "",
                                                       "Excel files (*.xlsx *.xls)")
            if file_path:
                df = pd.read_excel(file_path)
                for index, row in df.iterrows():
                    data = {
                        'type': str(row["Тип устройства"]),
                        'description': str(row["Сообщение о поломке"]),
                        'user': str(row["Человек (ФИО)"]),
                        'repairer_name': str(row["Ремонтник (ФИО)"]),
                        'time': str(row["Дата запроса"])
                    }
                    response = requests.post(f"{FLASK_URL}/receive", json=data, timeout=5)
                    if response.status_code != 200:
                        raise Exception(f"Ошибка сервера: {response.status_code}")
                QMessageBox.information(self, "Успех", "Данные загружены из файла")
                self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())