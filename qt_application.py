import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget, QToolBar, QAction, QDialog, QFormLayout, QLineEdit, QTextEdit,
    QPushButton, QComboBox, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer
import pandas as pd
import requests
from datetime import datetime

# URL Flask-сервера (замените на актуальный домен/IP и порт при хостинге)
FLASK_URL = "http://192.168.1.100:5000"  # При хостинге: "https://your-domain.com"


class RepairDialog(QDialog):
    def __init__(self, parent=None, data=None, device_types=None, manufacturers=None,
                 accessories=None):
        super().__init__(parent)
        self.setWindowTitle("Ремонт")
        self.layout = QFormLayout(self)

        # Списки для выпадающих меню
        self.device_types = device_types or ["Смартфон", "Планшет", "Ноутбук", "ПК", "Другое"]
        self.manufacturers = manufacturers or ["Apple", "Samsung", "Xiaomi", "HP", "Dell", "Другое"]
        self.accessories_list = accessories or ["Коробка", "Наушники", "Блок питания", "Другое"]
        self.statuses = ["принят", "сдан в ремонт", "готов", "выдан"]

        # Поля ввода
        self.client_name = QLineEdit(self)
        self.device_type = QComboBox(self)
        self.device_type.setEditable(True)
        self.device_type.addItems(self.device_types)
        self.manufacturer = QComboBox(self)
        self.manufacturer.setEditable(True)
        self.manufacturer.addItems(self.manufacturers)
        self.model = QLineEdit(self)
        self.serial_number = QLineEdit(self)
        self.accessories = QComboBox(self)
        self.accessories.setEditable(True)
        self.accessories.addItems(self.accessories_list)
        self.client_address = QLineEdit(self)
        self.status = QComboBox(self)
        self.status.addItems(self.statuses)
        self.issue_description = QTextEdit(self)
        self.issue_description.setFixedHeight(100)
        self.notes = QTextEdit(self)
        self.notes.setFixedHeight(100)

        # Добавление полей в форму
        self.layout.addRow("ФИО клиента:", self.client_name)
        self.layout.addRow("Тип устройства:", self.device_type)
        self.layout.addRow("Изготовитель:", self.manufacturer)
        self.layout.addRow("Модель:", self.model)
        self.layout.addRow("Серийный номер:", self.serial_number)
        self.layout.addRow("Комплектация:", self.accessories)
        self.layout.addRow("Адрес клиента:", self.client_address)
        self.layout.addRow("Статус:", self.status)
        self.layout.addRow("Неисправность:", self.issue_description)
        self.layout.addRow("Примечания:", self.notes)

        self.save_button = QPushButton("Сохранить", self)
        self.save_button.clicked.connect(self.accept)
        self.layout.addWidget(self.save_button)

        if data:
            self.client_name.setText(data[0])
            self.device_type.setCurrentText(data[1])
            self.manufacturer.setCurrentText(data[2])
            self.model.setText(data[3])
            self.serial_number.setText(data[4])
            self.accessories.setCurrentText(data[5])
            self.client_address.setText(data[6])
            self.status.setCurrentText(data[7])
            self.issue_description.setText(data[9])
            self.notes.setText(data[10])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Учет ремонтов")
        self.resize(1800, 800)

        # Инициализация списков для пользовательских значений
        self.custom_device_types = ["Смартфон", "Планшет", "Ноутбук", "ПК", "Другое"]
        self.custom_manufacturers = ["Apple", "Samsung", "Xiaomi", "HP", "Dell", "Другое"]
        self.custom_accessories = ["Коробка", "Наушники", "Блок питания", "Другое"]

        self.table = QTableWidget(self)
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels(
            [
                "ID", "ФИО клиента", "Тип устройства", "Изготовитель", "Модель",
                "Серийный номер", "Комплектация", "Адрес клиента", "Статус",
                "Время статуса", "Неисправность", "Примечания", "Действия"
            ]
        )
        self.table.setColumnHidden(0, True)
        self.table.cellDoubleClicked.connect(self.edit_record)
        self.table.cellClicked.connect(self.show_issue_description)
        column_widths = [0, 150, 150, 150, 150, 150, 150, 150, 100, 150, 200, 200, 100]
        for i, width in enumerate(column_widths):
            self.table.setColumnWidth(i, width)
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

                # Обновляем списки пользовательских значений
                new_device_types = set(self.custom_device_types)
                new_manufacturers = set(self.custom_manufacturers)
                new_accessories = set(self.custom_accessories)

                for row in rows:
                    if row['device_type'] and row['device_type'] not in new_device_types:
                        new_device_types.add(row['device_type'])
                    if row['manufacturer'] and row['manufacturer'] not in new_manufacturers:
                        new_manufacturers.add(row['manufacturer'])
                    if row['accessories'] and row['accessories'] not in new_accessories:
                        new_accessories.add(row['accessories'])

                # Обновляем списки
                self.custom_device_types = sorted(list(new_device_types))
                self.custom_manufacturers = sorted(list(new_manufacturers))
                self.custom_accessories = sorted(list(new_accessories))

                # Заполняем таблицу
                for i, row in enumerate(rows):
                    self.table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
                    self.table.setItem(i, 1, QTableWidgetItem(row['client_name']))
                    self.table.setItem(i, 2, QTableWidgetItem(row['device_type']))
                    self.table.setItem(i, 3, QTableWidgetItem(row['manufacturer']))
                    self.table.setItem(i, 4, QTableWidgetItem(row['model']))
                    self.table.setItem(i, 5, QTableWidgetItem(row['serial_number']))
                    self.table.setItem(i, 6, QTableWidgetItem(row['accessories']))
                    self.table.setItem(i, 7, QTableWidgetItem(row['client_address']))
                    self.table.setItem(i, 8, QTableWidgetItem(row['status']))
                    self.table.setItem(i, 9, QTableWidgetItem(row['status_timestamp']))
                    self.table.setItem(i, 10, QTableWidgetItem(row['issue_description']))
                    self.table.setItem(i, 11, QTableWidgetItem(row['notes']))
                    delete_button = QPushButton("Удалить")
                    delete_button.clicked.connect(
                        lambda checked, r=i, id=row['id']: self.delete_record(r, id))
                    self.table.setCellWidget(i, 12, delete_button)
            else:
                QMessageBox.critical(self, "Ошибка", f"Ошибка сервера: {response.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")

    def save_data(self):
        try:
            data = [[self.table.item(i, j).text() for j in range(1, 12)]
                    for i in range(self.table.rowCount())]
            df = pd.DataFrame(data, columns=[
                "ФИО клиента", "Тип устройства", "Изготовитель", "Модель",
                "Серийный номер", "Комплектация", "Адрес клиента", "Статус",
                "Время статуса", "Неисправность", "Примечания"
            ])
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "",
                                                       "Excel files (*.xlsx)")
            if file_path:
                df.to_excel(file_path, index=False)
                QMessageBox.information(self, "Успех", f"Данные выгружены в {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def add_record(self):
        dialog = RepairDialog(self, device_types=self.custom_device_types,
                              manufacturers=self.custom_manufacturers,
                              accessories=self.custom_accessories)
        if dialog.exec_():
            data = {
                'client_name': dialog.client_name.text(),
                'device_type': dialog.device_type.currentText(),
                'manufacturer': dialog.manufacturer.currentText(),
                'model': dialog.model.text(),
                'serial_number': dialog.serial_number.text(),
                'accessories': dialog.accessories.currentText(),
                'client_address': dialog.client_address.text(),
                'status': dialog.status.currentText(),
                'issue_description': dialog.issue_description.toPlainText(),
                'notes': dialog.notes.toPlainText()
            }
            try:
                response = requests.post(f"{FLASK_URL}/receive", json=data, timeout=5)
                if response.status_code == 200:
                    # Добавляем пользовательские значения в списки
                    if data['device_type'] and data['device_type'] not in self.custom_device_types:
                        self.custom_device_types.append(data['device_type'])
                        self.custom_device_types.sort()
                    if data['manufacturer'] and data[
                        'manufacturer'] not in self.custom_manufacturers:
                        self.custom_manufacturers.append(data['manufacturer'])
                        self.custom_manufacturers.sort()
                    if data['accessories'] and data['accessories'] not in self.custom_accessories:
                        self.custom_accessories.append(data['accessories'])
                        self.custom_accessories.sort()
                    QMessageBox.information(self, "Успех", "Запись добавлена")
                    self.load_data()
                else:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка сервера: {response.status_code}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись: {str(e)}")

    def edit_record(self, row, column):
        if column == 12:
            return
        id_item = self.table.item(row, 0)
        if id_item:
            record_id = int(id_item.text())
            data = [self.table.item(row, i).text() for i in range(1, 12)]
            dialog = RepairDialog(self, data, device_types=self.custom_device_types,
                                  manufacturers=self.custom_manufacturers,
                                  accessories=self.custom_accessories)
            if dialog.exec_():
                new_data = {
                    'client_name': dialog.client_name.text(),
                    'device_type': dialog.device_type.currentText(),
                    'manufacturer': dialog.manufacturer.currentText(),
                    'model': dialog.model.text(),
                    'serial_number': dialog.serial_number.text(),
                    'accessories': dialog.accessories.currentText(),
                    'client_address': dialog.client_address.text(),
                    'status': dialog.status.currentText(),
                    'issue_description': dialog.issue_description.toPlainText(),
                    'notes': dialog.notes.toPlainText()
                }
                try:
                    response = requests.delete(f"{FLASK_URL}/delete_repair/{record_id}", timeout=5)
                    if response.status_code != 200:
                        raise Exception(f"Ошибка удаления: {response.status_code}")
                    response = requests.post(f"{FLASK_URL}/receive", json=new_data, timeout=5)
                    if response.status_code == 200:
                        # Добавляем пользовательские значения в списки
                        if new_data['device_type'] and new_data[
                            'device_type'] not in self.custom_device_types:
                            self.custom_device_types.append(new_data['device_type'])
                            self.custom_device_types.sort()
                        if new_data['manufacturer'] and new_data[
                            'manufacturer'] not in self.custom_manufacturers:
                            self.custom_manufacturers.append(new_data['manufacturer'])
                            self.custom_manufacturers.sort()
                        if new_data['accessories'] and new_data[
                            'accessories'] not in self.custom_accessories:
                            self.custom_accessories.append(new_data['accessories'])
                            self.custom_accessories.sort()
                        QMessageBox.information(self, "Успех", "Запись обновлена")
                        self.load_data()
                    else:
                        raise Exception(f"Ошибка сервера: {response.status_code}")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось обновить запись: {str(e)}")

    def show_issue_description(self, row, column):
        if column == 10:
            issue = self.table.item(row, 10).text()
            QMessageBox.information(self, "Неисправность", issue)
        elif column == 11:
            notes = self.table.item(row, 11).text()
            QMessageBox.information(self, "Примечания", notes)

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
                    # Очищаем пользовательские списки, оставляя только начальные значения
                    self.custom_device_types = ["Смартфон", "Планшет", "Ноутбук", "ПК", "Другое"]
                    self.custom_manufacturers = ["Apple", "Samsung", "Xiaomi", "HP", "Dell",
                                                 "Другое"]
                    self.custom_accessories = ["Коробка", "Наушники", "Блок питания", "Другое"]
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
                        'client_name': str(row["ФИО клиента"]),
                        'device_type': str(row["Тип устройства"]),
                        'manufacturer': str(row["Изготовитель"]),
                        'model': str(row["Модель"]),
                        'serial_number': str(row["Серийный номер"]),
                        'accessories': str(row["Комплектация"]),
                        'client_address': str(row["Адрес клиента"]),
                        'status': str(row["Статус"]),
                        'issue_description': str(row["Неисправность"]),
                        'notes': str(row["Примечания"])
                    }
                    response = requests.post(f"{FLASK_URL}/receive", json=data, timeout=5)
                    if response.status_code != 200:
                        raise Exception(f"Ошибка сервера: {response.status_code}")
                    # Добавляем пользовательские значения в списки
                    if data['device_type'] and data['device_type'] not in self.custom_device_types:
                        self.custom_device_types.append(data['device_type'])
                        self.custom_device_types.sort()
                    if data['manufacturer'] and data[
                        'manufacturer'] not in self.custom_manufacturers:
                        self.custom_manufacturers.append(data['manufacturer'])
                        self.custom_manufacturers.sort()
                    if data['accessories'] and data['accessories'] not in self.custom_accessories:
                        self.custom_accessories.append(data['accessories'])
                        self.custom_accessories.sort()
                QMessageBox.information(self, "Успех", "Данные загружены из файла")
                self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())