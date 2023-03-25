'''
@author Jeremy G. Wilson

Copyright 2022 Jeremy G. Wilson

This file is a part of the Weekly Giving program (v.1.1)

Weekly Giving is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License (GNU GPL)
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

The Weekly Giving program includes Artifex Software's GhostScript,
licensed under the GNU Affero General Public License (GNU AGPL). See
https://www.ghostscript.com/licensing/index.html for more information.
'''

import json
import logging
import sqlite3
import sys
from datetime import datetime
from os.path import exists
import os
import shutil

from PyQt5.QtCore import QDate, Qt, QRegExp
from PyQt5.QtWidgets import QApplication, QFileDialog, QDialog, QGridLayout, QCalendarWidget, QPushButton, QLabel, \
    QMessageBox, QButtonGroup, QRadioButton, QWidget, QHBoxLayout, QLineEdit, QTextEdit, QVBoxLayout, QSpinBox

from gui import GUI


class WeeklyGiving:
    app = None
    DATABASE = None
    table_name = None
    gui = None
    ids = None
    dates = None
    spec_designations = None
    column_pairs = None
    current_id_index = None
    startup = None
    
    def __init__(self, app):
        self.app = app

        # Check to see if config file exists in user's APPDATA folder
        appData = os.getenv('APPDATA')

        new_dir = False
        if not exists(appData + '/WeeklyGiving'):
            new_dir = True
            os.mkdir(appData + '/WeeklyGiving')
            with open(appData + '/WeeklyGiving/log.txt', 'w') as file:
                pass

        if new_dir:
            self.write_log('Creating %APPDATA%/WeeklyGiving folder and log.txt')

        self.write_log('APPDATA location: ' + appData)

        self.config_file_loc = appData + '/WeeklyGiving/config.json'
        self.write_log('Config file location: ' + self.config_file_loc)

        if not exists(self.config_file_loc): # Copy default config file if not found
            self.write_log('Copying config file to APPDATA folder')
            shutil.copy('resources/default_config.json', self.config_file_loc)

        # read the config file as json
        self.write_log('Opening config file from ' + self.config_file_loc)
        with open(self.config_file_loc, 'r') as file:
            config_json = json.loads(file.read())
        file_loc = config_json['fileLoc']
        self.spec_designations = config_json['specialDesignations']
        self.max_checks = config_json['maxChecks']
        self.name = config_json['name']

        if exists(file_loc):
            self.DATABASE = file_loc
            self.table_name = 'weekly_giving'
            self.write_log('Database located at ' + self.DATABASE)
        else:
            response = QMessageBox.question(
                None,
                'File Not Found',
                'Database file not found. Would you like to locate it? (Choose "No" to create a new database)',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            self.write_log('Response to locating database file: ' + str(response))

            if response == QMessageBox.Yes:
                file_dialog = QFileDialog()
                file_dialog.setModal(True)
                db_file = file_dialog.getOpenFileName(None, 'Open Database File', appData, 'SQLite .db File (*.db)')

                self.DATABASE = db_file[0]
                self.table_name = 'weekly_giving'
                config_json['fileLoc'] = db_file[0]
                with open(self.config_file_loc, 'w') as file:
                    file.write(json.dumps(config_json))
            elif response == QMessageBox.No:
                self.DATABASE = appData + '/WeeklyGiving/weekly_giving.db'
                self.table_name = 'weekly_giving'

                config_json['fileLoc'] = self.DATABASE
                with open(self.config_file_loc, 'w') as file:
                    file.write(json.dumps(config_json))

                sql = '''
                    CREATE TABLE "weekly_giving" (
                    "id"	INTEGER,
                    "date"	TEXT,
                    "prepared_by"	TEXT,
                    "bills_100"	TEXT,
                    "bills_50"	TEXT,
                    "bills_20"	TEXT,
                    "bills_10"	TEXT,
                    "bills_5"	TEXT,
                    "bills_1"	TEXT,
                    "coins_100"	TEXT,
                    "coins_25"	TEXT,
                    "coins_10"	TEXT,
                    "coins_5"	TEXT,
                    "coins_1"	TEXT,
                    "spec1"	TEXT,
                    "spec2"	TEXT,
                    "spec3"	TEXT,
                    "spec4"	TEXT,
                    "spec5"	TEXT,
                    "spec6"	TEXT,
                    "spec7"	TEXT,
                    "checks_0"	TEXT,
                    "checks_1"	TEXT,
                    "checks_2"	TEXT,
                    "checks_3"	TEXT,
                    "checks_4"	TEXT,
                    "checks_5"	TEXT,
                    "checks_6"	TEXT,
                    "checks_7"	TEXT,
                    "checks_8"	TEXT,
                    "checks_9"	TEXT,
                    "checks_10"	TEXT,
                    "checks_11"	TEXT,
                    "checks_12"	TEXT,
                    "checks_13"	TEXT,
                    "checks_14"	TEXT,
                    "checks_15"	TEXT,
                    "checks_16"	TEXT,
                    "checks_17"	TEXT,
                    "checks_18"	TEXT,
                    "checks_19"	TEXT,
                    "checks_20"	TEXT,
                    "checks_21"	TEXT,
                    "checks_22"	TEXT,
                    "checks_23"	TEXT,
                    "checks_24"	TEXT,
                    "checks_25"	TEXT,
                    "checks_26"	TEXT,
                    "checks_27"	TEXT,
                    "checks_28"	TEXT,
                    "checks_29"	TEXT,
                    "notes"	TEXT,
                    "quantity_of_checks"	TEXT,
                    "total_designated_offerings"	TEXT,
                    "bills_total"	TEXT,
                    "coins_total"	TEXT,
                    "checks_total"	TEXT,
                    "total_deposit"	TEXT,
                    PRIMARY KEY("id" AUTOINCREMENT)
                )
                '''
                conn = sqlite3.connect(self.DATABASE)
                cursor = conn.cursor()
                cursor.execute(sql)
                conn.commit()
                conn.close()

                date = datetime.today().strftime('%Y-%m-%d')

                values = '"0",'
                for i in range(1, 58):
                    if i == 1:
                        values += '"' + date + '",'
                    elif i == 2 or i == 51:
                        values += '"",'
                    else:
                        values += '"0",'

                values = values[0:len(values) - 1]

                try:
                    conn = sqlite3.connect(self.DATABASE)
                    cur = conn.cursor()
                    sql = 'INSERT INTO ' + self.table_name + ' values (' + values + ')'
                    cur.execute(sql)
                    conn.commit()
                    conn.close()
                except (sqlite3.OperationalError, sqlite3.DatabaseError, sqlite3.NotSupportedError) as err:
                    self.write_log('*Critical error from WeeklyGiving.__init__: ' + str(err))
            else:
                quit()

        self.column_pairs = self.get_column_pairs(self.spec_designations)

        self.ids = self.get_ids()

        self.write_log('Starting GUI')
        self.gui = GUI(self)
        self.get_last_rec()

    def run_app(self):
        return self.app.exec()

    def get_ids(self):
        self.write_log('Retreiving ID list')
        conn = sqlite3.connect(self.DATABASE)
        cur = conn.cursor()
        ex = cur.execute('SELECT ID FROM ' + self.table_name)
        result = ex.fetchall()
        conn.close()

        ids = []
        for id in result:
            ids.append(id[0])
        return ids
    
    def get_dates(self):
        self.write_log('Retreiving Date List')
        conn = sqlite3.connect(self.DATABASE)
        cur = conn.cursor()
        result = cur.execute('SELECT Date, ID FROM ' + self.table_name).fetchall()
        dates = []
        conn.close()

        for date in result:
            dates.append(date)
        return dates

    def get_column_pairs(self, json):
        self.write_log('Getting special designation column pairs')

        keys = list(json.keys())
        pairs = []
        for item in keys:
            pairs.append([item, json[item]])

        return pairs
    
    def get_by_id(self, id):
        for i in range(len(self.ids)):
            if str(self.ids[i]) == str(id):
                self.current_id_index = i

        goon = self.check_for_changes()
        if goon:
            self.write_log('Retrieving record by ID: ' + str(id))

            try:
                con = sqlite3.connect(self.DATABASE)
                cur = con.cursor()
                sql = 'SELECT * FROM ' + self.table_name + ' WHERE id = ' + str(self.ids[self.current_id_index])
                ex = cur.execute(sql)
                column_names = [description[0] for description in ex.description]
                result = ex.fetchall()[0]
                con.close()

                result_dictionary = {column_names[i]: result[i] for i in range(len(column_names))}

                self.gui.fill_values(result_dictionary)

                if self.current_id_index > 0:
                    self.gui.prev_rec_button.setEnabled(True)
                else:
                    self.gui.prev_rec_button.setEnabled(False)

                if self.current_id_index < len(self.ids) - 1:
                    self.gui.next_rec_button.setEnabled(True)
                else:
                    self.gui.next_rec_button.setEnabled(False)

                self.gui.changes = False
                self.gui.save_button.setEnabled(False)

            except (sqlite3.OperationalError, sqlite3.DatabaseError, sqlite3.NotSupportedError) as err:
                self.write_log('*Critical error from WeeklyGiving.get_by_id: ' + str(err))

    def get_first_rec(self):
        goon = self.check_for_changes()
        if goon:
            self.current_id_index = 0
            self.get_by_id(self.ids[self.current_id_index])
            
    def get_prev_rec(self):
        goon = self.check_for_changes()
        if goon:
            self.current_id_index -= 1
            self.get_by_id(self.ids[self.current_id_index])
        
    def get_next_rec(self):
        goon = self.check_for_changes()
        if goon:
            self.current_id_index += 1
            self.get_by_id(self.ids[self.current_id_index])
        
    def get_last_rec(self):
        goon = self.check_for_changes()
        if goon:
            self.current_id_index = len(self.ids) - 1
            self.get_by_id(self.ids[self.current_id_index])
        
    def create_new_rec(self):
        goon = self.check_for_changes()
        if goon:
            newID = self.ids[len(self.ids) - 1] + 1
            from datetime import datetime
            date = datetime.today().strftime('%Y-%m-%d')

            values = '"' + str(newID) + '",'
            for i in range(1, 58):
                if i == 1:
                    values += '"' + date + '",'
                elif i == 2 or i == 51:
                    values += '"",'
                else:
                    values += '"0",'

            values = values[0:len(values) - 1]

            try:
                conn = sqlite3.connect(self.DATABASE)
                cur = conn.cursor()
                sql = 'INSERT INTO ' + self.table_name + ' values (' + values + ')'
                self.write_log('Insert command from WeeklyGiving.create_new_rec: ' + sql)
                cur.execute(sql)
                conn.commit()

                self.gui.id_combo_box.addItem(str(newID))
                self.gui.date_combo_box.addItem(date, (1, newID))
                self.ids.append(newID)

                self.get_by_id(newID)

                self.gui.changes = False
                self.gui.save_button.setEnabled(False)
            except (sqlite3.OperationalError, sqlite3.DatabaseError, sqlite3.NotSupportedError) as err:
                self.write_log('*Critical error from WeeklyGiving.get_by_id: ' + str(err))

    def del_rec(self):
        response = QMessageBox.question(
            None,
            'Delete Record',
            'Really delete this record? This action cannot be undone.',
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )

        if response == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(self.DATABASE)
                cur = conn.cursor()
                sql = 'DELETE FROM ' + self.table_name + ' WHERE ID = ' + self.gui.id_num_label.text()
                cur.execute(sql)
                conn.commit()

                self.ids = self.get_ids()
                self.gui.refresh_combo_boxes()

                self.get_last_rec()

                self.gui.next_rec_button.setEnabled(False)

                if not self.gui.prev_rec_button.isEnabled():
                    self.gui.prev_rec_button.setEnabled(True)

                self.gui.changes = False
                self.gui.save_button.setEnabled(False)

            except (sqlite3.OperationalError, sqlite3.DatabaseError, sqlite3.NotSupportedError) as err:
                self.write_log('*Critical error from WeeklyGiving.get_by_id: ' + str(err))
        
    def save_rec(self):
        sql = 'UPDATE ' + self.table_name + ' SET '
        sql += 'id = "' + self.gui.id_num_label.text()
        sql += '", prepared_by = "' + self.gui.prep_line_edit.text()
        sql += '", date = "' + self.gui.date_line_edit.text()

        sql += '", bills_100 = "' + self.gui.bills_100_line_edit.text()
        sql += '", bills_50 = "' + self.gui.bills_50_line_edit.text()
        sql += '", bills_20 = "' + self.gui.bills_20_line_edit.text()
        sql += '", bills_10 = "' + self.gui.bills_10_line_edit.text()
        sql += '", bills_5 = "' + self.gui.bills_5_line_edit.text()
        sql += '", bills_1 = "' + self.gui.bills_1_line_edit.text()

        sql += '", coins_100 = "' + self.gui.dollar_line_edit.text()
        sql += '", coins_25 = "' + self.gui.quarter_line_edit.text()
        sql += '", coins_10 = "' + self.gui.dime_line_edit.text()
        sql += '", coins_5 = "' + self.gui.nickel_line_edit.text()
        sql += '", coins_1 = "' + self.gui.penny_line_edit.text()

        counter = 1
        for widget in self.gui.findChildren(QLineEdit, 'special_edit'):
            sql += '", spec' + str(counter) + ' = "' + widget.text()
            counter += 1

        counter = 0
        for widget in self.gui.findChildren(QLineEdit, QRegExp('check*')):
            sql += '", checks_' + str(counter) + ' = "' + widget.text()
            counter += 1
        sql += '", quantity_of_checks = "' + self.gui.num_checks_total_label.text()

        sql += '", coins_total = "' + self.gui.coins_total_label.text()
        sql += '", bills_total = "' + self.gui.bills_total_label.text()
        sql += '", checks_total = "' + self.gui.checks_total_label.text()
        sql += '", total_designated_offerings = "' + self.gui.designated_total_label.text()
        sql += '", total_deposit = "' + self.gui.total_total_label.text()

        notes = self.gui.notes_edit.toPlainText()
        notes = notes.replace('"', '<apost>')
        notes = notes.replace('\'', '<quot>')
        sql += '", notes = "' + notes
        sql += '" WHERE id = ' + self.gui.id_num_label.text() + ';'

        self.write_log('WeeklyGiving.save_rec sql: ' + sql)

        try:
            conn = sqlite3.connect(self.DATABASE)
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()

            self.gui.changes = False
            self.gui.save_button.setEnabled(False)

        except (sqlite3.OperationalError, sqlite3.DatabaseError, sqlite3.NotSupportedError) as err:
            self.write_log('*Critical error from WeeklyGiving.get_by_id: ' + str(err))
        
    def check_for_changes(self):
        if self.gui.changes:
            print('asking to save')
            response = QMessageBox.question(
                None,
                'Changes Detected',
                'Save changes before proceeding?',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if response == QMessageBox.Yes:
                self.save_rec()
                return True
            elif response == QMessageBox.No:
                return True
            else:
                return False
        else:
            return True

    def change_designations(self):
        dialog = QDialog()
        layout = QGridLayout()
        dialog.setLayout(layout)

        row = 0

        title_label = QLabel('Make Changes to Special Designations:')
        layout.addWidget(title_label, row, 0, 1, 2)
        row += 1

        for item in self.column_pairs:
            line_edit = QLineEdit(item[1])
            layout.addWidget(line_edit, row, 0)
            row += 1

        ok_button = QPushButton('OK')
        ok_button.pressed.connect(lambda: dialog.done(0))
        layout.addWidget(ok_button, row, 0)

        cancel_button = QPushButton('Cancel')
        cancel_button.pressed.connect(lambda: dialog.done(1))
        layout.addWidget(cancel_button, row, 1)
        result = dialog.exec()

        if result == 0:
            designations = []
            for widget in dialog.findChildren(QLineEdit):
                designations.append(widget.text())

            try:
                with open(self.config_file_loc, 'r') as file:
                    config_json = json.loads(file.read())

                for i in range(len(designations)):
                    config_json['specialDesignations']['spec' + str(i + 1)] = str(designations[i])

                with open(self.config_file_loc, 'w') as file:
                    file.write(json.dumps(config_json))

                self.gui.rewrite_designations(designations)

            except OSError as err:
                self.write_log('*Critical error from WeeklyGiving.change_designations: ' + str(err))

    def change_name(self):
        try:
            dialog = QDialog()
            layout = QVBoxLayout()
            dialog.setLayout(layout)

            label = QLabel('Change Church Name:')
            layout.addWidget(label)

            line_edit = QLineEdit(self.name)
            layout.addWidget(line_edit)

            button_widget = QWidget()
            button_layout = QHBoxLayout()
            button_widget.setLayout(button_layout)

            ok_button = QPushButton('OK')
            ok_button.setFixedWidth(100)
            ok_button.pressed.connect(lambda: dialog.done(0))
            button_layout.addWidget(ok_button)

            cancel_button = QPushButton('Cancel')
            cancel_button.setFixedWidth(100)
            cancel_button.pressed.connect(lambda: dialog.done(1))
            button_layout.addWidget(cancel_button)

            layout.addWidget(button_widget)

            result = dialog.exec()
        except Exception:
            logging.exception('')

        if result == 0:
            try:
                self.name = line_edit.text()
                with open(self.config_file_loc, 'r') as file:
                    config_json = json.loads(file.read())

                config_json['name'] = self.name

                with open(self.config_file_loc, 'w') as file:
                    file.write(json.dumps(config_json))

                self.gui.main_title_label.setText(self.name + ' Weekly Giving Report')

            except OSError as err:
                self.write_log('*Critical error in WeeklyGiving.change_name: ' + str(err))

    def change_num_checks(self):
        dialog = QDialog()
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        change_widget = QWidget()
        change_layout = QHBoxLayout()
        change_widget.setLayout(change_layout)

        label = QLabel('Change Maximum Number of Checks:')
        change_layout.addWidget(label)

        spin_box = QSpinBox()
        spin_box.setRange(5, 200)
        spin_box.setValue(self.max_checks)
        change_layout.addWidget(spin_box)

        layout.addWidget(change_widget)

        button_widget = QWidget()
        button_layout = QHBoxLayout()
        button_widget.setLayout(button_layout)

        ok_button = QPushButton('OK')
        ok_button.setFixedWidth(100)
        ok_button.pressed.connect(lambda: dialog.done(0))
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton('Cancel')
        cancel_button.setFixedWidth(100)
        cancel_button.pressed.connect(lambda: dialog.done(1))
        button_layout.addWidget(cancel_button)

        layout.addWidget(button_widget)

        result = dialog.exec()

        if result == 0:
            new_max_checks = spin_box.value()
            try:
                with open(self.config_file_loc, 'r') as file:
                    config_json = json.loads(file.read())

                config_json['maxChecks'] = new_max_checks

                with open(self.config_file_loc, 'w') as file:
                    file.write(json.dumps(config_json))

                conn = sqlite3.connect(self.DATABASE)
                cur = conn.cursor()
                result = cur.execute('SELECT * FROM ' + self.table_name + ' WHERE id=' + str(self.ids[0]))
                column_names = [description[0] for description in result.description]

                highest_num = -1
                for column in column_names:
                    if 'check' in column and not 'quantity' in column and not 'tot' in column:
                        column_split = column.split('checks_')
                        if int(column_split[1]) > highest_num:
                            highest_num = int(column_split[1])

                if new_max_checks > highest_num + 1:
                    added_columns = []
                    for i in range(highest_num, new_max_checks - 1):
                        new_column = 'checks_' + str(i + 1)
                        added_columns.append(new_column)
                        sql = 'ALTER TABLE ' + self.table_name + ' ADD COLUMN ' + new_column + ' TEXT;'
                        cur.execute(sql)
                        conn.commit()

                    for column in added_columns:
                        sql = 'UPDATE ' + self.table_name + ' SET ' + column + ' = "0.00"'
                        cur.execute(sql)
                        conn.commit()

                    conn.close()

                elif new_max_checks <= highest_num:
                    response = QMessageBox.question(
                        self.gui,
                        'Confirm Delete Columns',
                        'You have chosen a maxumum number of checks that is fewer than you have now. If you have '
                        'previously saved information in those higher check numbers, it will be irretrievablty '
                        'lost. Continue?',
                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                    )

                    if response == QMessageBox.Yes:
                        for i in range(new_max_checks, highest_num + 1):
                            sql = 'ALTER TABLE ' + self.table_name + ' DROP COLUMN "checks_' + str(i) + '";'
                            cur.execute(sql)
                            conn.commit()
                        conn.close()

                #QMessageBox.information(self.gui, 'Restart Required', 'Restart the program to complete the change.')
                self.app.exit(1517)

            except OSError as err:
                self.write_log('*Critical error in WeeklyGiving.change_name: ' + str(err))
            except Exception:
                logging.exception('')

    def save_to_new_loc(self):
        file = QFileDialog().getSaveFileName(
            self.gui,
            'Save to New Location',
            os.path.expanduser('~'), 'SQLite .db file (*.db)'
        )

        if file[0]:
            import shutil
            file_loc = file[0]
            self.write_log('New database file location: ' + file_loc)

            try:
                shutil.copy(self.DATABASE, file_loc)
                self.DATABASE = file_loc

                with open(self.config_file_loc, 'r') as file:
                    config_json = json.loads(file.read())

                config_json['fileLoc'] = file_loc

                with open(self.config_file_loc, 'w') as file:
                    file.write(json.dumps(config_json))

            except OSError as err:
                self.write_log('*Critical error from WeeklyGiving.save_to_new_loc: ' + str(err))
            
    def do_backup(self):
        pathArray = self.DATABASE.split('/')
        databaseDir = ''
        for i in range(0, len(pathArray) - 1):
            databaseDir += pathArray[i] + '/'

        try:
            fileArray = os.listdir(databaseDir)
            backupFiles = []
            for file in fileArray:
                if 'backup' in file:
                    backupFiles.append(file)

            if(len(backupFiles) >= 5):
                os.remove(databaseDir + backupFiles[0])

            from datetime import datetime
            now = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
            newBackupFile = databaseDir + pathArray[len(pathArray) - 1] + '.backup.' + now
            self.write_log('New Backup File: ' + newBackupFile)

            import shutil
            shutil.copy(self.DATABASE, newBackupFile)

        except OSError as err:
            self.write_log('Error from WeeklyGiving.do_backup: ' + str(err))
        
    def write_log(self, text):
        try:
            if '*Critical' in text:
                QMessageBox().critical(
                    self.gui,
                    'Error',
                    'A critical error has occurred. Try again, or view the log at\n'
                        + os.getenv("APPDATA")
                        + 'log.txt for more information.\n\n'
                        + text,
                    QMessageBox.Ok
                )
            logFileLoc = os.getenv('APPDATA') + '/WeeklyGiving/log.txt'
            logfile = open(logFileLoc, 'a')
            logfile.write(str(datetime.today()) + ': ' + text + '\n')
            logfile.close()
        except Exception:
            logging.exception('')

    def view_log(self):
        try:
            with open(os.getenv('APPDATA') + '/WeeklyGiving/log.txt', 'r') as file:
                log_text = file.read()
        except OSError as err:
            self.write_log('*Critical error from WeeklyGiving.change_designations: ' + str(err))

        self.log_dialog = QWidget()
        self.log_dialog.setMinimumSize(600, 600)
        log_layout = QVBoxLayout()
        self.log_dialog.setLayout(log_layout)

        log_text_edit = QTextEdit()
        log_text_edit.setReadOnly(True)
        log_text_edit.setLineWrapMode(QTextEdit.NoWrap)
        log_text_edit.setText(log_text)
        log_layout.addWidget(log_text_edit)

        ok_button = QPushButton('OK')
        ok_button.setMaximumWidth(50)
        ok_button.pressed.connect(self.log_dialog.close)
        log_layout.addWidget(ok_button)

        self.log_dialog.show()

    def graph_by_date(self):
        dialog = QDialog()
        layout = QGridLayout()
        dialog.setLayout(layout)

        start_label = QLabel('Choose Start Date:')
        start_label.setFont(self.gui.bold_font)
        layout.addWidget(start_label, 0, 0)

        start_date = QCalendarWidget()
        layout.addWidget(start_date, 1, 0)

        end_label = QLabel('Choose End Date:')
        end_label.setFont(self.gui.bold_font)
        layout.addWidget(end_label, 0, 1)

        end_date = QCalendarWidget()
        layout.addWidget(end_date, 1, 1)

        button_group = QButtonGroup()
        button_widget = QWidget()
        button_layout = QHBoxLayout()
        button_widget.setLayout(button_layout)

        button_label = QLabel('Graph Type:')
        button_label.setFont(self.gui.bold_font)
        button_layout.addWidget(button_label)

        line_button = QRadioButton('Line Graph')
        line_button.setFont(self.gui.plain_font)
        button_group.addButton(line_button)
        button_layout.addWidget(line_button)

        bar_button = QRadioButton('Bar Graph')
        bar_button.setFont(self.gui.plain_font)
        button_group.addButton(bar_button)
        button_layout.addWidget(bar_button)

        layout.addWidget(button_widget, 2, 0)
        line_button.setChecked(True)

        go_button = QPushButton('Go')
        go_button.setMaximumWidth(100)
        go_button.pressed.connect(lambda: dialog.done(1))
        layout.addWidget(go_button, 3, 0, Qt.AlignRight)

        cancel_button = QPushButton('Cancel')
        cancel_button.setMaximumWidth(100)
        cancel_button.pressed.connect(lambda: dialog.done(0))
        layout.addWidget(cancel_button, 3, 1)

        answer = dialog.exec()

        if answer == 1:
            start = start_date.selectedDate()
            end = end_date.selectedDate()
            connection = sqlite3.connect(self.DATABASE)
            cursor = connection.cursor()
            sql = 'SELECT Date, Total_Deposit from ' + self.table_name
            result = cursor.execute(sql).fetchall()

            filtered_dates = []
            for item in result:
                date_split = item[0].split('-')
                date = QDate(int(date_split[0]), int(date_split[1]), int(date_split[2]))
                if date >= start and date <= end:
                    filtered_dates.append(item)

            if len(filtered_dates) > 0:
                try:
                    from graphThis import LineGraph
                    lg = LineGraph(filtered_dates)
                    if line_button.isChecked():
                        lg.graph_values_by_date_line()
                    else:
                        lg.graph_values_by_date_bar()
                except Exception:
                    logging.exception('')


lwg = None
if __name__ == '__main__':
    exit_code = 1517
    while exit_code == 1517:
        app = QApplication(sys.argv)
        if lwg:
            lwg.gui.destroy()
        lwg = WeeklyGiving(app)
        exit_code = lwg.run_app()
