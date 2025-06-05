import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, \
    QWidget, QToolBar, QAction, QDialog, QFormLayout, QLineEdit, QTextEdit, QPushButton, QDateEdit, \
    QMessageBox, QFileDialog
from PyQt5.QtCore import QDate, Qt
import sqlite3
import pandas as pd


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
        self.resize(1200, 800)  # Увеличение размера окна
        self.table = QTableWidget(self)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Тип устройства", "Сообщение о поломке", "Человек (ФИО)", "Ремонтник (ФИО)",
             "Дата запроса", "Действия"])
        self.table.setColumnHidden(0, True)
        self.table.cellDoubleClicked.connect(self.edit_record)
        self.table.cellClicked.connect(self.show_issue_description)

        # Установка ширины столбцов
        self.table.setColumnWidth(1, 200)  # Тип устройства
        self.table.setColumnWidth(2, 300)  # Сообщение о поломке
        self.table.setColumnWidth(3, 200)  # Человек (ФИО)
        self.table.setColumnWidth(4, 200)  # Ремонтник (ФИО)
        self.table.setColumnWidth(5, 150)  # Дата запроса
        self.table.setColumnWidth(6, 100)  # Действия

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

        self.conn = sqlite3.connect("repairs.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS repairs (
                id INTEGER PRIMARY KEY,
                device_type TEXT,
                issue_description TEXT,
                client_name TEXT,
                repairer_name TEXT,
                request_date DATE
            )
        """)
        self.conn.commit()
        self.load_data()

    def load_data(self):
        self.cursor.execute("SELECT * FROM repairs")
        rows = self.cursor.fetchall()
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            for j, col in enumerate(row[1:6]):
                self.table.setItem(i, j + 1, QTableWidgetItem(str(col)))
            delete_button = QPushButton("Удалить")
            delete_button.clicked.connect(lambda checked, r=i: self.delete_record(r))
            self.table.setCellWidget(i, 6, delete_button)

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
            data = (
                dialog.device_type.text(),
                dialog.issue_description.toPlainText(),
                dialog.client_name.text(),
                dialog.repairer_name.text(),
                dialog.request_date.date().toString("yyyy-MM-dd")
            )
            self.cursor.execute(
                "INSERT INTO repairs (device_type, issue_description, client_name, repairer_name, request_date) VALUES (?, ?, ?, ?, ?)",
                data)
            self.conn.commit()
            self.load_data()

    def edit_record(self, row, column):
        if column == 6:
            return
        id_item = self.table.item(row, 0)
        if id_item:
            record_id = int(id_item.text())
            data = [self.table.item(row, i).text() for i in range(1, 6)]
            dialog = RepairDialog(self, data)
            if dialog.exec_():
                new_data = (
                    dialog.device_type.text(),
                    dialog.issue_description.toPlainText(),
                    dialog.client_name.text(),
                    dialog.repairer_name.text(),
                    dialog.request_date.date().toString("yyyy-MM-dd"),
                    record_id
                )
                self.cursor.execute(
                    "UPDATE repairs SET device_type=?, issue_description=?, client_name=?, repairer_name=?, request_date=? WHERE id=?",
                    new_data)
                self.conn.commit()
                self.load_data()

    def show_issue_description(self, row, column):
        if column == 2:
            issue = self.table.item(row, 2).text()
            QMessageBox.information(self, "Сообщение о поломке", issue)

    def delete_record(self, row):
        id_item = self.table.item(row, 0)
        if id_item:
            record_id = int(id_item.text())
            self.cursor.execute("DELETE FROM repairs WHERE id=?", (record_id,))
            self.conn.commit()
            self.load_data()

    def delete_all_records(self):
        reply = QMessageBox.question(self, "Подтверждение",
                                     "Вы уверены, что хотите удалить все записи?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.cursor.execute("DELETE FROM repairs")
            self.conn.commit()
            self.load_data()

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
                    data = (
                        row["Тип устройства"],
                        row["Сообщение о поломке"],
                        row["Человек (ФИО)"],
                        row["Ремонтник (ФИО)"],
                        row["Дата запроса"]
                    )
                    self.cursor.execute(
                        "INSERT INTO repairs (device_type, issue_description, client_name, repairer_name, request_date) "
                        "VALUES (?, ?, ?, ?, ?)", data
                    )
                self.conn.commit()
                self.load_data()
                QMessageBox.information(self, "Успех", "Данные загружены из файла")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())