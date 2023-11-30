'''
@author Jeremy G. Wilson

Copyright 2022 Jeremy G. Wilson

This file is a part of the Weekly Giving program (v.1.4)

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
import time
from datetime import datetime
from os.path import exists
import os
import shutil

from PyQt5.QtCore import QDate, Qt, QRegExp, QRunnable, QObject, QThreadPool, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QFileDialog, QDialog, QGridLayout, QCalendarWidget, QPushButton, QLabel, \
    QMessageBox, QButtonGroup, QRadioButton, QWidget, QHBoxLayout, QLineEdit, QTextEdit, QVBoxLayout, QSpinBox

from gui import GUI


class WeeklyGiving(QObject):
    start_gui = pyqtSignal()
    app = None
    DATABASE = None
    table_name = None
    gui = None
    ids = None
    dates = None
    spec_designations = None
    column_pairs = None
    current_id_index = None
    thread_pool = None

    def __init__(self):
        super().__init__()
        self.start_gui.connect(self.init_gui)

        self.thread_pool = QThreadPool()
        self.startup = Startup(self)
        self.thread_pool.start(self.startup)

    def init_gui(self):
        """
        Instantiates gui.GUI and calls its create_gui signal. Loads the last record in the database.
        """
        self.gui = GUI(self, self.name)
        self.gui.create_gui.emit()
        self.get_last_rec()

    def get_ids(self):
        """
        Stores all id numbers from the Database into a list then returns that list
        """
        try:
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
        except Exception:
            logging.exception('')
    
    def get_dates(self):
        """
        Stores all dates from the Database into a list then returns the list
        """
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
        """
        Gets the key:value pairs from the configuration json and returns the list containing them
        :param json json: the JSON object of configuration settings
        """
        try:
            self.write_log('Getting special designation column pairs')

            keys = list(json.keys())
            pairs = []
            for item in keys:
                pairs.append([item, json[item]])

            return pairs
        except Exception:
            logging.exception('')
    
    def get_by_id(self, id):
        """
        Finds a given id number in the list of ids and pulls that id's data from the database. Sends that data
        to the gui's fill_values method.
        :param int id: ID number of the desired record
        """
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

            except (sqlite3.OperationalError, sqlite3.DatabaseError, sqlite3.NotSupportedError, IndexError) as err:
                self.write_log('*Critical error from WeeklyGiving.get_by_id: ' + str(err))

    def get_first_rec(self):
        """
        Sets current_id_index to zero and calls get_by_id based on that index of self.ids
        """
        goon = self.check_for_changes()
        if goon:
            self.current_id_index = 0
            self.get_by_id(self.ids[self.current_id_index])
            
    def get_prev_rec(self):
        """
        Sets current_id_index to one less than it is currently then calls get_by_id based on that index of self.ids
        """
        goon = self.check_for_changes()
        if goon:
            self.current_id_index -= 1
            self.get_by_id(self.ids[self.current_id_index])
        
    def get_next_rec(self):
        """
        Sets current_id_index to one more than it is currently then calls get_by_id based on that index of self.ids
        """
        goon = self.check_for_changes()
        if goon:
            self.current_id_index += 1
            self.get_by_id(self.ids[self.current_id_index])
        
    def get_last_rec(self):
        """
        Sets current_id_index to the last index in the range of self.ids
        then calls get_by_id based on that index of self.ids
        """
        goon = self.check_for_changes()
        if goon:
            self.current_id_index = len(self.ids) - 1
            if not len(self.ids) == 0:
                self.get_by_id(self.ids[self.current_id_index])
            else:
                self.create_new_rec()
        
    def create_new_rec(self):
        """
        Creates a new ID number based on the highest ID number in self.ids. Applies today's date to that record
        and adds the record to the database.
        """
        goon = self.check_for_changes()
        if goon:
            if not len(self.ids) == 0:
                newID = self.ids[len(self.ids) - 1] + 1
            else:
                newID = 1

            from datetime import datetime
            date = datetime.today().strftime('%Y-%m-%d')

            values = '"' + str(newID) + '",'
            for i in range(1, self.max_checks + 28):
                if i == 1:
                    values += '"' + date + '",'
                elif i == 2 or i == 21 + self.max_checks:
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

                print('from create new rec:', self.ids, self.current_id_index)

                self.get_by_id(newID)

                self.gui.changes = False
                self.gui.save_button.setEnabled(False)
            except (sqlite3.OperationalError, sqlite3.DatabaseError, sqlite3.NotSupportedError) as err:
                self.write_log('*Critical error from WeeklyGiving.get_by_id: ' + str(err))

    def del_rec(self):
        """
        Asks user for confirmation to delete the current record then removes it from the database
        """
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
        """
        Gathers all of the data from the gui's entries and build a sql statment to update the record based on the
        current id number.
        """
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
        for widget in self.gui.findChildren(QLineEdit, QRegExp('special_edit*')):
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

            confirm_label = QLabel('Record Saved')
            confirm_label.setParent(self.gui)
            confirm_label.setFont(QFont('Helvetica', 32))
            confirm_label.setStyleSheet(
                'background: white; color: ' + self.gui.dark_green + '; padding: 10px; border: 5px solid ' + self.gui.dark_green + ';')
            confirm_label.adjustSize()
            confirm_label.move(
                int((self.gui.width() / 2) - confirm_label.width() / 2),
                int((self.gui.height() / 2) - confirm_label.width() / 2))
            confirm_label.show()
            QApplication.processEvents()
            time.sleep(1.0)
            confirm_label.hide()
            confirm_label.deleteLater()

        except (sqlite3.OperationalError, sqlite3.DatabaseError, sqlite3.NotSupportedError) as err:
            self.write_log('*Critical error from WeeklyGiving.get_by_id: ' + str(err))
        
    def check_for_changes(self):
        """
        Method to provide a dialog asking user to save if there have been changes to the current record. Returns True
        or False depending on user's answer.
        """
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
        """
        Provides a QDialog containing QLineEdits of all special designation labels. Saves any changes the user
        makes to those labels in the config file.
        """
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

    def include_special(self, sender):
        """
        Sets the include_special_in_total variable and saves changes to the config file.
        :param QObject sender: The checkable menu action
        """
        if sender.isChecked():
            self.include_special_in_total = True
        else:
            self.include_special_in_total = False

        try:
            with open(self.config_file_loc, 'r') as file:
                config_json = json.loads(file.read())

            config_json['includeSpecial'] = self.include_special_in_total

            with open(self.config_file_loc, 'w') as file:
                file.write(json.dumps(config_json))

        except OSError as err:
            self.write_log('*Critical error in WeeklyGiving.include_special: ' + str(err))

    def change_name(self):
        """
        Provides the user with a dialog where they can change the church name shown in the program and on the
        printout.
        """
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
        """
        Provides the user with a dialog to change the number of check fields shown in the GUI
        """
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
            self.max_checks = new_max_checks
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
                    # make sure the user knows that if at any time there have been more checks recorded than the
                    # current maximum shown, they will be lost.
                    response = QMessageBox.question(
                        self.gui,
                        'Confirm Delete Columns',
                        'You have chosen a maxumum number of checks that is fewer than you have now. If you have '
                        'previously saved information in those higher check numbers, it will be irretrievablty '
                        'lost. Continue?',
                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                    )

                    if response == QMessageBox.Yes:
                        # drop any superfluous check columns
                        for i in range(new_max_checks, highest_num + 1):
                            sql = 'ALTER TABLE ' + self.table_name + ' DROP COLUMN "checks_' + str(i) + '";'
                            cur.execute(sql)
                            conn.commit()
                        conn.close()

                # save the current listing of check values to be inserted into the rebuilt checks_widget
                check_values = []
                for widget in self.gui.checks_widget.findChildren(QLineEdit):
                    check_values.append(widget.text())

                # remove and rebuild the gui's checks_widget to reflect the new number of checks
                self.gui.main_layout.removeWidget(self.gui.checks_widget)
                self.gui.main_layout.update()
                self.gui.build_checks_frame()
                QApplication.processEvents()

                index = 0
                for widget in self.gui.checks_widget.findChildren(QLineEdit):
                    if index < len(check_values) and widget:
                        widget.setText(check_values[index])
                    index += 1

            except OSError as err:
                self.write_log('*Critical error in WeeklyGiving.change_num_checks: ' + str(err))
            except Exception:
                logging.exception('')

    def save_to_new_loc(self):
        """
        Opens a QFileDialog for the user to save the database to a new location. Changes the location stored in
        the config file.
        """
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
        """
        Writes a backup file to the user's database directory, appending the current date and time to the file name.
        Removes oldest file if there are already 5 or more backup files.
        """
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
        """
        Saves a given block of text to the log file. Alternatively, will also show the user a dialog if logging a
        critical, error, or file error. Appends the current date and time to the given text.
        :param str text: The text to be logged
        """
        text = text.split('\r\n')
        formatted_text = ''

        for i in range(len(text)):
            if len(text[i].strip()) > 0:
                if i < 1:
                    formatted_text += text[i]
                else:
                    formatted_text += '\r\n\t' + text[i]

        try:
            if '*Critical' in text:
                QMessageBox().critical(
                    self.gui,
                    'Error',
                    'A critical error has occurred. Try again, or view the log at\n'
                        + os.getenv("APPDATA")
                        + 'log.txt for more information.\n\n'
                        + formatted_text,
                    QMessageBox.Ok
                )
            elif '*File' in text:
                QMessageBox().critical(
                    self.gui,
                    'Error',
                    'Database file not found. Exiting.',
                    QMessageBox.Ok
                )
            elif '*Error' in text:
                QMessageBox().warning(
                    self.gui,
                    'Error',
                    'An error has occurred:\n\n' + text + '\n\nTry again, or view the log at\n'
                        + os.getenv("APPDATA")
                        + 'log.txt for more information.\n\n'
                        + formatted_text,
                    QMessageBox.Ok
                )
            logFileLoc = os.getenv('APPDATA') + '/WeeklyGiving/log.txt'
            logfile = open(logFileLoc, 'a')
            logfile.write(str(datetime.today()) + ': ' + formatted_text + '\n')
            logfile.close()
        except Exception:
            logging.exception('')

    def view_log(self):
        """
        Method to enable viewing of the log file from within the program
        """
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
        """
        Provides the user with a dialog where they can choose a date range from which to graph deposits. Creates and
        shows a line graph by calling graph_this.LineGraph.
        """
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
            from graph_this import LineGraph
            lg = LineGraph()
            QApplication.processEvents()

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
            print(line_button.isChecked())

            if len(filtered_dates) > 0:
                try:
                    if line_button.isChecked():
                        lg.pairs = filtered_dates
                        lg.graph_values_by_date_line()
                    else:
                        print('creating bar graph')
                        lg.pairs = filtered_dates
                        lg.graph_values_by_date_bar()
                except Exception:
                    logging.exception('')


class Startup(QRunnable):
    """
    Class impolementing QRunnable to perform all of the startup tasks of the program, making use of loading_box's
    change_text signal to provide visual updates on the progress. Goes pretty quick. May not be necessary.
    """
    def __init__(self, wg):
        super().__init__()
        self.wg = wg
        self.loading_box = LoadingBox(wg)

    def run(self):
        try:
            # Check to see if config file exists in user's APPDATA folder
            self.loading_box.change_text.emit('Getting Directories')
            self.wg.appData = os.getenv('APPDATA')
            new_dir = False
            if not exists(self.wg.appData + '/WeeklyGiving'):
                new_dir = True
                os.mkdir(self.wg.appData + '/WeeklyGiving')
                with open(self.wg.appData + '/WeeklyGiving/log.txt', 'w') as file:
                    pass

            if new_dir:
                self.wg.write_log('Creating %APPDATA%/WeeklyGiving folder and log.txt')

            self.wg.write_log('APPDATA location: ' + self.wg.appData)

            self.loading_box.change_text.emit('Checking Files')
            self.wg.config_file_loc = self.wg.appData + '/WeeklyGiving/config.json'
            self.wg.write_log('Config file location: ' + self.wg.config_file_loc)

            if not exists(self.wg.config_file_loc): # Copy default config file if not found
                self.wg.write_log('Copying config file to APPDATA folder')
                shutil.copy('resources/default_config.json', self.wg.config_file_loc)

            # read the config file as json
            self.wg.write_log('Opening config file from ' + self.wg.config_file_loc)
            with open(self.wg.config_file_loc, 'r') as file:
                self.wg.config_json = json.loads(file.read())
            self.wg.file_loc = self.wg.config_json['fileLoc']
            self.wg.spec_designations = self.wg.config_json['specialDesignations']
            self.wg.max_checks = self.wg.config_json['maxChecks']
            self.wg.name = self.wg.config_json['name']
            self.wg.include_special_in_total = self.wg.config_json['includeSpecial']

            self.loading_box.change_text.emit('Checking Database')
            self.loading_box.check_database_signal.emit()
            while self.loading_box.checking:
                pass

            self.loading_box.change_text.emit('Starting GUI')

            self.loading_box.end.emit()
            self.wg.start_gui.emit()

        except Exception as ex:
            self.wg.write_log('*Critical error from Startup.run: ' + str(ex))


class LoadingBox(QDialog):
    """
    Class implementing QDialog to provide user with updates on the initial startup progress.
    """
    change_text = pyqtSignal(str)
    check_database_signal = pyqtSignal()
    end = pyqtSignal()
    checking = True

    def __init__(self, wg):
        """
        :param WeeklyGiving wg: The WeeklyGiving instance
        """
        super().__init__()
        self.wg = wg
        self.change_text.connect(self.change_label_text)
        self.check_database_signal.connect(self.check_database)
        self.end.connect(lambda: self.done(0))
        self.init_components()

    def init_components(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setStyleSheet('background-color: #00641e')

        layout = QGridLayout()
        self.setLayout(layout)

        self.status_label = QLabel('Starting...')
        self.status_label.setAutoFillBackground(False)
        self.status_label.setFont(QFont('Helvetica', 16, QFont.Bold))
        self.status_label.setStyleSheet('color: white')
        layout.addWidget(self.status_label, 0, 0)

        self.show()
        QApplication.processEvents()

    def change_label_text(self, text):
        """
        Method to be called when change_label signal is emitted. Updates the status_label with the given text.
        """
        self.status_label.setText(text)
        QApplication.processEvents()

    def check_database(self):
        """
        Method to check that the database exists. Gives the user options to create a new database or to find an old
        one if it doesn't exist.
        """
        if exists(self.wg.file_loc):
            self.wg.DATABASE = self.wg.file_loc
            self.wg.table_name = 'weekly_giving'
            self.wg.write_log('Database located at ' + self.wg.DATABASE)
        else:
            try:
                response = QMessageBox.question(
                    None,
                    'File Not Found',
                    'Database file not found. Would you like to locate it? (Choose "No" to create a new database)',
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
                print(str(response))
                self.wg.write_log('Response to locating database file: ' + str(response))
            except Exception:
                logging.exception('')

            if response == QMessageBox.Yes:
                file_dialog = QFileDialog()
                file_dialog.setModal(True)
                db_file = file_dialog.getOpenFileName(
                    None,
                    'Open Database File',
                    self.wg.appData,
                    'SQLite .db File (*.db)'
                )

                self.wg.DATABASE = db_file[0]
                self.wg.table_name = 'weekly_giving'
                self.wg.config_json['fileLoc'] = db_file[0]
                with open(self.wg.config_file_loc, 'w') as file:
                    file.write(json.dumps(self.wg.config_json))
            elif response == QMessageBox.No:
                try:
                    print('setting db file loc and table name')
                    self.wg.DATABASE = self.wg.appData + '/WeeklyGiving/weekly_giving.db'
                    self.wg.table_name = 'weekly_giving'
                    print('dumping config_json to file')
                    self.wg.config_json['fileLoc'] = self.wg.DATABASE
                    with open(self.wg.config_file_loc, 'w') as file:
                        file.write(json.dumps(self.wg.config_json))

                    print('creating sql')
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

                    print('executing sql')
                    conn = sqlite3.connect(self.wg.DATABASE)
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
                        conn = sqlite3.connect(self.wg.DATABASE)
                        cur = conn.cursor()
                        sql = 'INSERT INTO ' + self.wg.table_name + ' values (' + values + ')'
                        cur.execute(sql)
                        conn.commit()
                        conn.close()
                    except (sqlite3.OperationalError, sqlite3.DatabaseError, sqlite3.NotSupportedError) as err:
                        self.wg.write_log('*Critical error from GUI.check_database: ' + str(err))
                except TypeError:
                    self.wg.write_log('Database file not found. Exiting.')
            else:
                quit()

        self.wg.column_pairs = self.wg.get_column_pairs(self.wg.spec_designations)

        self.wg.ids = self.wg.get_ids()
        self.checking = False


class Recalc(QRunnable):
    """
    Implements QRunnable to perform the calculations required to update the gui's totals area.
    """
    def __init__(self, all_values, gui):
        """
        :param list all_values: all values from the gui's fields
        :param GUI gui: the GUI instance
        """
        super().__init__()
        self.all_values = all_values
        self.gui = gui

    def run(self):
        bill_values = [100, 50, 20, 10, 5, 1]
        coin_values = [1.0, 0.25, 0.10, 0.05, 0.01]
        bills_tot = 0.0
        coins_tot = 0.0
        special_tot = 0.0
        checks_tot = 0.0
        num_checks = 0

        for i in range(0, 6):
            if len(self.all_values[i]) > 0:
                try:
                    bills_tot += float(self.all_values[i]) * bill_values[i]
                except ValueError:
                    pass

        for i in range(6, 11):
            if len(self.all_values[i]) > 0:
                try:
                    coins_tot += float(self.all_values[i]) * coin_values[i - 6]
                except ValueError:
                    pass

        for i in range(11, 18):
            if len(self.all_values[i]) > 0:
                try:
                    special_tot += float(self.all_values[i].replace(',', ''))
                except ValueError as ex:
                    self.gui.lwg.write_log('*Error: ' + str(ex))
                    pass

        for i in range(18, len(self.all_values)):
            if len(self.all_values[i]) > 0:
                try:
                    checks_tot += float(self.all_values[i].replace(',', ''))
                    num_checks += 1
                except ValueError:
                    self.gui.lwg.write_log('*Error: ' + str(ex))
                    pass

        totals = [bills_tot, coins_tot, special_tot, checks_tot, num_checks]
        self.gui.set_total_labels.emit(totals)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    WeeklyGiving()
    app.exec()
