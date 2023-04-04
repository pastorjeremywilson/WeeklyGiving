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
import os
import sqlite3
import subprocess
from datetime import datetime
from os.path import exists

from dateutil.parser import parse, ParserError
from PyQt5.QtCore import QRegExp, Qt
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QLineEdit, \
    QTextEdit, QVBoxLayout, QScrollArea, QMessageBox, QTextBrowser, QFileDialog


class GUI(QMainWindow):
    changes = None
    main_title_label = None

    def __init__(self, lwg, name='LBC of Nampa', num_checks=30):
        self.lwg = lwg
        self.name = name
        self.num_checks = num_checks

        self.plain_font = QFont('Helvetica', 11)
        self.bold_font = QFont('Helvetica', 11, QFont.Bold)
        self.title_font = QFont('Helvetica', 16, QFont.Bold)
        self.light_green = '#eaffe8'
        self.dark_green = '#00641e'

        success = self.check_database()

        if success:
            super().__init__()
            self.init_components()
            self.showMaximized()
            self.changes = False
            self.save_button.setEnabled(False)

    def closeEvent(self, event):
        event.ignore()
        if self.changes:
            result = QMessageBox.question(
                self,
                'Changes Detected',
                'Changes have been made. Save before Closing?',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

            if result == QMessageBox.Yes:
                self.lwg.save_rec()
                self.lwg.do_backup()
                event.accept()
            elif result == QMessageBox.No:
                self.lwg.do_backup()
                event.accept()
            else:
                event.ignore()
        else:
            self.lwg.do_backup()
            event.accept()

    def check_database(self):
        if exists(self.lwg.file_loc):
            self.lwg.DATABASE = self.lwg.file_loc
            self.lwg.table_name = 'weekly_giving'
            self.lwg.write_log('Database located at ' + self.lwg.DATABASE)
        else:
            response = QMessageBox.question(
                None,
                'File Not Found',
                'Database file not found. Would you like to locate it? (Choose "No" to create a new database)',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            self.lwg.write_log('Response to locating database file: ' + str(response))

            if response == QMessageBox.Yes:
                file_dialog = QFileDialog()
                file_dialog.setModal(True)
                db_file = file_dialog.getOpenFileName(
                    None,
                    'Open Database File',
                    self.lwg.appData,
                    'SQLite .db File (*.db)'
                )

                self.lwg.DATABASE = db_file[0]
                self.lwg.table_name = 'weekly_giving'
                self.lwg.config_json['fileLoc'] = db_file[0]
                with open(self.lwg.config_file_loc, 'w') as file:
                    file.write(json.dumps(self.lwg.config_json))
            elif response == QMessageBox.No:
                self.lwg.DATABASE = self.lwg.appData + '/WeeklyGiving/weekly_giving.db'
                self.lwg.table_name = 'weekly_giving'

                self.lwg.config_json['fileLoc'] = self.lwg.DATABASE
                with open(self.lwg.config_file_loc, 'w') as file:
                    file.write(json.dumps(self.lwg.config_json))

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
                conn = sqlite3.connect(self.lwg.DATABASE)
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
                    conn = sqlite3.connect(self.lwg.DATABASE)
                    cur = conn.cursor()
                    sql = 'INSERT INTO ' + self.lwg.table_name + ' values (' + values + ')'
                    cur.execute(sql)
                    conn.commit()
                    conn.close()
                except (sqlite3.OperationalError, sqlite3.DatabaseError, sqlite3.NotSupportedError) as err:
                    self.lwg.write_log('*Critical error from GUI.check_database: ' + str(err))
            else:
                quit()

        self.lwg.column_pairs = self.lwg.get_column_pairs(self.lwg.spec_designations)

        self.lwg.ids = self.lwg.get_ids()
        return(True)

    def init_components(self):
        self.setWindowTitle('Weekly Giving')
        self.setWindowIcon(QIcon('resources/icon.ico'))

        main_widget = QWidget()
        main_widget.setStyleSheet('background-color: ' + self.dark_green)
        self.setCentralWidget(main_widget)

        self.main_layout = QGridLayout()
        self.main_layout.setRowStretch(0, 1)
        self.main_layout.setRowStretch(1, 1)
        self.main_layout.setRowStretch(2, 1)
        self.main_layout.setRowStretch(3, 1)
        self.main_layout.setRowStretch(4, 1)
        self.main_layout.setRowStretch(5, 10)
        self.main_layout.setColumnStretch(0, 1)
        self.main_layout.setColumnStretch(1, 1)
        self.main_layout.setColumnStretch(2, 1)
        self.main_layout.setColumnStretch(3, 2)
        main_widget.setLayout(self.main_layout)

        self.main_title_label = QLabel(self.lwg.name + ' Weekly Giving Report')
        self.main_title_label.setFont(self.title_font)
        self.main_title_label.setStyleSheet('color: white')
        self.main_layout.addWidget(self.main_title_label, 0, 0)

        self.build_menu_bar()
        self.build_top_frame()
        self.build_info_frame()
        self.build_bills_frame()
        self.build_coins_frame()
        self.build_checks_frame()
        self.build_special_frame()
        self.build_notes_frame()
        self.build_totals_frame()

    def build_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('File')

        save_action = file_menu.addAction('Save Record')
        save_action.triggered.connect(self.lwg.save_rec)

        print_action = file_menu.addAction('Print')
        print_action.triggered.connect(self.print_rec)

        file_menu.addSeparator()

        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)

        tools_menu = menu_bar.addMenu('Tools')

        new_action = tools_menu.addAction('New Record')
        new_action.triggered.connect(self.lwg.create_new_rec)

        delete_action = tools_menu.addAction('Delete Record')
        delete_action.triggered.connect(self.lwg.del_rec)

        log_action = tools_menu.addAction('View Log File')
        log_action.triggered.connect(self.lwg.view_log)

        config_menu = menu_bar.addMenu('Settings')

        name_action = config_menu.addAction('Change Church Name')
        name_action.triggered.connect(self.lwg.change_name)

        spec_offering_action = config_menu.addAction('Change Special Offering Designations')
        spec_offering_action.triggered.connect(self.lwg.change_designations)

        num_checks_action = config_menu.addAction('Change Maximum Number of Checks')
        num_checks_action.triggered.connect(self.lwg.change_num_checks)

        new_loc_action = config_menu.addAction('Save Database to New Location')
        new_loc_action.triggered.connect(self.lwg.save_to_new_loc)

        help_menu = menu_bar.addMenu('Help')

        help_action = help_menu.addAction('Help')
        help_action.triggered.connect(self.show_help)

        about_action = help_menu.addAction('About')
        about_action.triggered.connect(self.show_about)

    def build_top_frame(self):
        top_widget = QWidget()
        top_widget.setObjectName('top_widget')
        top_widget.setStyleSheet('#top_widget { background-color: ' + self.dark_green + '; border-top: 3px solid white; border-bottom: 3px solid white;}')
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 10, 0, 10)
        top_widget.setLayout(top_layout)

        first_rec_button = QPushButton()
        first_rec_button.setIcon(QIcon('resources/firstrec.png'))
        first_rec_button.setToolTip('Go to the first record')
        first_rec_button.setStyleSheet('padding: 10px; background-color: ' + self.light_green)
        first_rec_button.setMaximumWidth(40)
        first_rec_button.pressed.connect(self.lwg.get_first_rec)
        top_layout.addWidget(first_rec_button)

        self.prev_rec_button = QPushButton()
        self.prev_rec_button.setIcon(QIcon('resources/prevrec.png'))
        self.prev_rec_button.setToolTip('Go to the previous record')
        self.prev_rec_button.setStyleSheet('padding: 10px; background-color: ' + self.light_green)
        self.prev_rec_button.setMaximumWidth(40)
        self.prev_rec_button.pressed.connect(self.lwg.get_prev_rec)
        top_layout.addWidget(self.prev_rec_button)

        self.next_rec_button = QPushButton()
        self.next_rec_button.setIcon(QIcon('resources/nextrec.png'))
        self.next_rec_button.setToolTip('Go to the next record')
        self.next_rec_button.setStyleSheet('padding: 10px; background-color: ' + self.light_green)
        self.next_rec_button.setMaximumWidth(40)
        self.next_rec_button.pressed.connect(self.lwg.get_next_rec)
        top_layout.addWidget(self.next_rec_button)

        last_rec_button = QPushButton()
        last_rec_button.setIcon(QIcon('resources/lastrec.png'))
        last_rec_button.setToolTip('Go to the last record')
        last_rec_button.setStyleSheet('padding: 10px; background-color: ' + self.light_green)
        last_rec_button.setMaximumWidth(40)
        last_rec_button.pressed.connect(self.lwg.get_last_rec)
        top_layout.addWidget(last_rec_button)

        new_rec_button = QPushButton()
        new_rec_button.setIcon(QIcon('resources/newrec.png'))
        new_rec_button.setToolTip('Create a new record')
        new_rec_button.setStyleSheet('padding: 10px; background-color: ' + self.light_green)
        new_rec_button.setMaximumWidth(40)
        new_rec_button.pressed.connect(self.lwg.create_new_rec)
        top_layout.addWidget(new_rec_button)

        top_layout.addStretch(1)

        id_label = QLabel('Choose Record by ID:')
        id_label.setFont(self.bold_font)
        id_label.setStyleSheet('color: white')
        top_layout.addWidget(id_label)

        self.id_combo_box = QComboBox()
        self.id_combo_box.setFont(self.plain_font)
        self.id_combo_box.setMinimumWidth(50)
        self.id_combo_box.setStyleSheet('background-color: white; border: 1px solid white;')
        self.id_combo_box.currentIndexChanged.connect(lambda: self.lwg.get_by_id(self.id_combo_box.currentText()))
        top_layout.addWidget(self.id_combo_box)

        date_label = QLabel('Choose Record by Date:')
        date_label.setFont(self.bold_font)
        date_label.setStyleSheet('color: white')
        top_layout.addWidget(date_label)

        self.date_combo_box = QComboBox()
        self.date_combo_box.setFont(self.plain_font)
        self.date_combo_box.setMinimumWidth(120)
        self.date_combo_box.setStyleSheet('background-color: white; border: 1px solid white;')
        self.date_combo_box.currentIndexChanged.connect(lambda: self.lwg.get_by_id(self.date_combo_box.currentData()[1]))
        top_layout.addWidget(self.date_combo_box)

        self.refresh_combo_boxes()

        top_layout.addStretch(1)

        print_rec_button = QPushButton()
        print_rec_button.setIcon(QIcon('resources/printrec.png'))
        print_rec_button.setToolTip('Print this record')
        print_rec_button.setStyleSheet('padding: 10px; background-color: ' + self.light_green)
        print_rec_button.setMaximumWidth(40)
        print_rec_button.pressed.connect(self.print_rec)
        top_layout.addWidget(print_rec_button)
        top_layout.addSpacing(10)

        graph_button = QPushButton()
        graph_button.setIcon(QIcon('resources/graph.png'))
        graph_button.setToolTip('Create a graph of giving within a date range')
        graph_button.setStyleSheet('padding: 10px; background-color: ' + self.light_green)
        graph_button.setMaximumWidth(40)
        graph_button.pressed.connect(self.lwg.graph_by_date)
        top_layout.addWidget(graph_button)
        top_layout.addSpacing(10)

        self.save_button = QPushButton()
        self.save_button.setIcon(QIcon('resources/saverec.png'))
        self.save_button.setToolTip('Save Record')
        self.save_button.setStyleSheet('padding: 10px; background-color: ' + self.light_green)
        self.save_button.setMaximumWidth(40)
        self.save_button.pressed.connect(self.lwg.save_rec)
        top_layout.addWidget(self.save_button)

        self.main_layout.addWidget(top_widget, 1, 0, 1, 4)

    def build_info_frame(self):
        info_widget = QWidget()
        info_widget.setStyleSheet('background-color: ' + self.light_green)

        info_layout = QHBoxLayout()
        info_widget.setLayout(info_layout)

        id_label = QLabel('ID:')
        id_label.setFont(self.bold_font)
        info_layout.addWidget(id_label)

        self.id_num_label = QLabel()
        self.id_num_label.setFont(self.plain_font)
        info_layout.addWidget(self.id_num_label)

        date_label = QLabel('Date:')
        date_label.setFont(self.bold_font)
        info_layout.addWidget(date_label)

        self.date_line_edit = CustomDateLineEdit()
        self.date_line_edit.setFont(self.plain_font)
        info_layout.addWidget(self.date_line_edit)

        prep_label = QLabel('Prepared By:')
        prep_label.setFont(self.bold_font)
        info_layout.addWidget(prep_label)

        self.prep_line_edit = QLineEdit()
        self.prep_line_edit.setFont(self.plain_font)
        self.prep_line_edit.setMinimumWidth(300)
        info_layout.addWidget(self.prep_line_edit)

        info_layout.addStretch(1)

        self.main_layout.addWidget(info_widget, 2, 0, 1, 4)

    def build_bills_frame(self):
        bills_widget = QWidget()
        bills_widget.setStyleSheet('background-color: ' + self.light_green)

        bills_layout = QGridLayout()
        bills_widget.setLayout(bills_layout)

        bills_label = QLabel('Bills')
        bills_label.setFont(self.bold_font)
        bills_label.setStyleSheet('color: ' + self.dark_green)
        bills_label.setMinimumHeight(30)
        bills_layout.addWidget(bills_label, 0, 0)

        bills_100_label = QLabel('Hundreds')
        bills_100_label.setFont(self.plain_font)
        bills_layout.addWidget(bills_100_label, 1, 0)

        self.bills_100_line_edit = CustomIntegerLineEdit()
        self.bills_100_line_edit.setFont(self.plain_font)
        self.bills_100_line_edit.textEdited.connect(self.on_change)
        bills_layout.addWidget(self.bills_100_line_edit, 1, 1)

        bills_50_label = QLabel('Fifties')
        bills_50_label.setFont(self.plain_font)
        bills_layout.addWidget(bills_50_label, 2, 0)

        self.bills_50_line_edit = CustomIntegerLineEdit()
        self.bills_50_line_edit.setFont(self.plain_font)
        self.bills_50_line_edit.textEdited.connect(self.on_change)
        bills_layout.addWidget(self.bills_50_line_edit, 2, 1)

        bills_20_label = QLabel('Twenties')
        bills_20_label.setFont(self.plain_font)
        bills_layout.addWidget(bills_20_label, 3, 0)

        self.bills_20_line_edit = CustomIntegerLineEdit()
        self.bills_20_line_edit.setFont(self.plain_font)
        self.bills_20_line_edit.textEdited.connect(self.on_change)
        bills_layout.addWidget(self.bills_20_line_edit, 3, 1)

        bills_10_label = QLabel('Tens')
        bills_10_label.setFont(self.plain_font)
        bills_layout.addWidget(bills_10_label, 4, 0)

        self.bills_10_line_edit = CustomIntegerLineEdit()
        self.bills_10_line_edit.setFont(self.plain_font)
        self.bills_10_line_edit.textEdited.connect(self.on_change)
        bills_layout.addWidget(self.bills_10_line_edit, 4, 1)

        bills_5_label = QLabel('Fives')
        bills_5_label.setFont(self.plain_font)
        bills_layout.addWidget(bills_5_label, 5, 0)

        self.bills_5_line_edit = CustomIntegerLineEdit()
        self.bills_5_line_edit.setFont(self.plain_font)
        self.bills_5_line_edit.textEdited.connect(self.on_change)
        bills_layout.addWidget(self.bills_5_line_edit, 5, 1)

        bills_1_label = QLabel('Ones')
        bills_1_label.setFont(self.plain_font)
        bills_layout.addWidget(bills_1_label, 6, 0)

        self.bills_1_line_edit = CustomIntegerLineEdit()
        self.bills_1_line_edit.setFont(self.plain_font)
        self.bills_1_line_edit.textEdited.connect(self.on_change)
        bills_layout.addWidget(self.bills_1_line_edit, 6, 1)

        self.main_layout.addWidget(bills_widget, 3, 0)

    def build_coins_frame(self):
        coins_widget = QWidget()
        coins_widget.setStyleSheet('background-color: ' + self.light_green)

        coins_layout = QGridLayout()
        coins_widget.setLayout(coins_layout)

        coins_label = QLabel('Coins')
        coins_label.setFont(self.bold_font)
        coins_label.setStyleSheet('color: ' + self.dark_green)
        coins_label.setMinimumHeight(30)
        coins_layout.addWidget(coins_label, 0, 0)

        dollar_label = QLabel('Dollars')
        dollar_label.setFont(self.plain_font)
        coins_layout.addWidget(dollar_label, 1, 0)

        self.dollar_line_edit = CustomIntegerLineEdit()
        self.dollar_line_edit.setFont(self.plain_font)
        self.dollar_line_edit.textEdited.connect(self.on_change)
        coins_layout.addWidget(self.dollar_line_edit, 1, 1)

        quarter_label = QLabel('Quarters')
        quarter_label.setFont(self.plain_font)
        coins_layout.addWidget(quarter_label, 2, 0)

        self.quarter_line_edit = CustomIntegerLineEdit()
        self.quarter_line_edit.setFont(self.plain_font)
        self.quarter_line_edit.textEdited.connect(self.on_change)
        coins_layout.addWidget(self.quarter_line_edit, 2, 1)

        dime_label = QLabel('Dimes')
        dime_label.setFont(self.plain_font)
        coins_layout.addWidget(dime_label, 3, 0)

        self.dime_line_edit = CustomIntegerLineEdit()
        self.dime_line_edit.setFont(self.plain_font)
        self.dime_line_edit.textEdited.connect(self.on_change)
        coins_layout.addWidget(self.dime_line_edit, 3, 1)

        nickel_label = QLabel('Nickels')
        nickel_label.setFont(self.plain_font)
        coins_layout.addWidget(nickel_label, 4, 0)

        self.nickel_line_edit = CustomIntegerLineEdit()
        self.nickel_line_edit.setFont(self.plain_font)
        self.nickel_line_edit.textEdited.connect(self.on_change)
        coins_layout.addWidget(self.nickel_line_edit, 4, 1)

        penny_label = QLabel('Pennies')
        penny_label.setFont(self.plain_font)
        coins_layout.addWidget(penny_label, 5, 0)

        self.penny_line_edit = CustomIntegerLineEdit()
        self.penny_line_edit.setFont(self.plain_font)
        self.penny_line_edit.textEdited.connect(self.on_change)
        coins_layout.addWidget(self.penny_line_edit, 5, 1)

        self.main_layout.addWidget(coins_widget, 4, 0)

    def build_special_frame(self):
        special_widget = QWidget()
        special_widget.setStyleSheet('background-color: ' + self.light_green)

        special_layout = QGridLayout()
        special_widget.setLayout(special_layout)

        special_label = QLabel('Special Designations')
        special_label.setStyleSheet('color: ' + self.dark_green)
        special_label.setFont(self.bold_font)
        special_label.setMinimumHeight(30)
        special_layout.addWidget(special_label, 0, 0)

        for i in range(0, len(self.lwg.spec_designations)):
            label = QLabel(self.lwg.column_pairs[i][1])
            label.setObjectName('special_label')
            label.setFont(self.plain_font)
            special_layout.addWidget(label, i + 1, 0)
            line_edit = CustomCurrencyLineEdit()
            line_edit.setFont(self.plain_font)
            line_edit.setObjectName('special_edit')
            line_edit.textEdited.connect(self.on_change)
            special_layout.addWidget(line_edit, i + 1, 1)

        self.main_layout.addWidget(special_widget, 3, 2)

    def build_checks_frame(self):
        checks_widget = QWidget()
        checks_widget.setStyleSheet('background-color: ' + self.light_green)

        checks_layout = QGridLayout()
        checks_widget.setLayout(checks_layout)

        checks_label = QLabel('Checks')
        checks_label.setFont(self.bold_font)
        checks_label.setStyleSheet('color: ' + self.dark_green)
        checks_label.setMinimumHeight(30)
        checks_layout.addWidget(checks_label, 0, 0)

        for i in range(0, self.lwg.max_checks):
            label = QLabel('Check ' + str(i + 1))
            label.setFont(self.plain_font)
            checks_layout.addWidget(label, i + 1, 0)
            line_edit = CustomCurrencyLineEdit()
            line_edit.setObjectName('checks_' + str(i))
            line_edit.setFont(self.plain_font)
            line_edit.textEdited.connect(self.on_change)
            checks_layout.addWidget(line_edit, i + 1, 1)

        scroll_container = QScrollArea()
        scroll_container.setStyleSheet('background-color: ' + self.light_green)
        scroll_container.setWidget(checks_widget)

        self.main_layout.addWidget(scroll_container, 3, 1, 3, 1)

    def build_notes_frame(self):
        notes_widget = QWidget()
        notes_widget.setStyleSheet('background-color: ' + self.light_green)

        notes_layout = QVBoxLayout()
        notes_widget.setLayout(notes_layout)

        notes_label = QLabel('Notes')
        notes_label.setFont(self.bold_font)
        notes_label.setStyleSheet('color: ' + self.dark_green)
        notes_label.setMinimumHeight(30)
        notes_layout.addWidget(notes_label)

        self.notes_edit = QTextEdit()
        self.notes_edit.setFont(self.plain_font)
        self.notes_edit.setStyleSheet('background-color: white')
        self.notes_edit.textChanged.connect(self.on_change)
        notes_layout.addWidget(self.notes_edit)

        self.main_layout.addWidget(notes_widget, 3, 3)

    def build_totals_frame(self):
        totals_widget = QWidget()
        totals_widget.setStyleSheet('background-color: ' + self.light_green)

        totals_layout = QGridLayout()
        totals_layout.setColumnStretch(2, 2)
        totals_layout.setRowMinimumHeight(3, 20)
        totals_layout.setRowMinimumHeight(7, 20)
        totals_widget.setLayout(totals_layout)

        totals_label = QLabel('Totals')
        totals_label.setFont(self.bold_font)
        totals_label.setStyleSheet('color: ' + self.dark_green)
        totals_label.setMinimumHeight(30)
        totals_layout.addWidget(totals_label, 0, 0)

        num_checks_label = QLabel('Number of Checks:')
        num_checks_label.setFont(self.bold_font)
        num_checks_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(num_checks_label, 1, 0)

        self.num_checks_total_label = QLabel()
        self.num_checks_total_label.setFont(self.plain_font)
        self.num_checks_total_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(self.num_checks_total_label, 1, 1)

        designated_label = QLabel('Total Designated Offerings:')
        designated_label.setFont(self.bold_font)
        designated_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(designated_label, 2, 0)

        self.designated_total_label = QLabel()
        self.designated_total_label.setFont(self.plain_font)
        self.designated_total_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(self.designated_total_label, 2, 1)

        bills_label = QLabel('Total Bills:')
        bills_label.setFont(self.bold_font)
        bills_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(bills_label, 4, 0)

        self.bills_total_label = QLabel()
        self.bills_total_label.setFont(self.plain_font)
        self.bills_total_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(self.bills_total_label, 4, 1)

        coins_label = QLabel('Total Coins:')
        coins_label.setFont(self.bold_font)
        coins_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(coins_label, 5, 0)

        self.coins_total_label = QLabel()
        self.coins_total_label.setFont(self.plain_font)
        self.coins_total_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(self.coins_total_label, 5, 1)

        checks_label = QLabel('Total Checks:')
        checks_label.setFont(self.bold_font)
        checks_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(checks_label, 6, 0)

        self.checks_total_label = QLabel()
        self.checks_total_label.setFont(self.plain_font)
        self.checks_total_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(self.checks_total_label, 6, 1)

        total_label = QLabel('Total:')
        total_label.setFont(self.bold_font)
        total_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(total_label, 8, 0)

        self.total_total_label = QLabel()
        self.total_total_label.setFont(self.bold_font)
        self.total_total_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(self.total_total_label, 8, 1)

        self.main_layout.addWidget(totals_widget, 4, 3)

    def on_change(self):
        self.changes = True
        self.save_button.setEnabled(True)
        self.recalc()

    def fill_values(self, result_dictionary):
        try:
            self.id_combo_box.blockSignals(True)
            self.date_combo_box.blockSignals(True)
            self.id_combo_box.setCurrentText(str(result_dictionary['id']))
            self.date_combo_box.setCurrentText(result_dictionary['date'])
            self.id_combo_box.blockSignals(False)
            self.date_combo_box.blockSignals(False)

            self.date_line_edit.setText(result_dictionary['date'])
            self.prep_line_edit.setText(result_dictionary['prepared_by'])
            self.id_num_label.setText(str(result_dictionary['id']))

            self.bills_100_line_edit.setText(result_dictionary['bills_100'])
            self.bills_50_line_edit.setText(result_dictionary['bills_50'])
            self.bills_20_line_edit.setText(result_dictionary['bills_20'])
            self.bills_10_line_edit.setText(result_dictionary['bills_10'])
            self.bills_5_line_edit.setText(result_dictionary['bills_5'])
            self.bills_1_line_edit.setText(result_dictionary['bills_1'])

            self.dollar_line_edit.setText(result_dictionary['coins_100'])
            self.quarter_line_edit.setText(result_dictionary['coins_25'])
            self.dime_line_edit.setText(result_dictionary['coins_10'])
            self.nickel_line_edit.setText(result_dictionary['coins_5'])
            self.penny_line_edit.setText(result_dictionary['coins_1'])

            specials = []
            for key in result_dictionary:
                if 'spec' in key:
                    specials.append(result_dictionary[key])

            index = 0
            for widget in self.findChildren(QLineEdit, 'special_edit'):
                widget.setText(str('{:.2f}'.format(float(specials[index]))))
                index += 1

            for key in result_dictionary:
                if 'check' in key and not 'quantity' in key and not 'tot' in key:
                    self.findChild(QLineEdit, key).setText(str('{:,.2f}'.format((float(result_dictionary[key].replace(',', ''))))))

            notes = result_dictionary['notes']
            notes = notes.replace('<apost>', '\'')
            notes = notes.replace('<quot>', '\"')
            self.notes_edit.setPlainText(notes)

            self.num_checks_total_label.setText(str(result_dictionary['quantity_of_checks']))

            self.recalc()

            self.changes = False
        except Exception:
            logging.exception('')

    def recalc(self):
        hundreds, fifties, twenties, tens, fives, ones = 0, 0, 0, 0, 0, 0
        if self.bills_100_line_edit.text().isdigit():
            hundreds = int(self.bills_100_line_edit.text())
        if self.bills_50_line_edit.text().isdigit():
            fifties = int(self.bills_50_line_edit.text())
        if self.bills_20_line_edit.text().isdigit():
            twenties = int(self.bills_20_line_edit.text())
        if self.bills_10_line_edit.text().isdigit():
            tens = int(self.bills_10_line_edit.text())
        if self.bills_5_line_edit.text().isdigit():
            fives = int(self.bills_5_line_edit.text())
        if self.bills_1_line_edit.text().isdigit():
            ones = int(self.bills_1_line_edit.text())

        bills_total = float((hundreds * 100) + (fifties * 50) + (twenties * 20) + (tens * 10) + (fives * 5) + ones)

        dollars, quarters, dimes, nickels, pennies = 0, 0, 0, 0, 0
        if self.dollar_line_edit.text().isdigit():
            dollars = int(self.dollar_line_edit.text())
        if self.quarter_line_edit.text().isdigit():
            quarters = int(self.quarter_line_edit.text())
        if self.dime_line_edit.text().isdigit():
            dimes = int(self.dime_line_edit.text())
        if self.nickel_line_edit.text().isdigit():
            nickels = int(self.nickel_line_edit.text())
        if self.penny_line_edit.text().isdigit():
            pennies = int(self.penny_line_edit.text())

        coins_total = float(dollars + (quarters * 0.25) + (dimes * 0.1) + (nickels * 0.05) + (pennies * 0.01))

        index = 0
        checks_total = 0.0
        num_checks = 0
        for widget in self.findChildren(QLineEdit, QRegExp('check*')):
            try:
                amount = widget.text().replace(',', '')
                checks_total += float(amount)
                if float(amount) > 0:
                    num_checks += 1
                index += 1
            except ValueError:
                if len(amount) > 0:
                    QMessageBox.information(self, 'Bad Number', 'Check number '
                                            + str(index + 1)
                                            + ' appears to contain a bad value. Check that '
                                              'it contains no letters or spaces')

        special_total = 0.0
        for widget in self.findChildren(QLineEdit, 'special_edit'):
            try:
                amount = widget.text().replace(',', '')
                special_total += float(amount)
            except ValueError:
                if len(amount) > 0:
                    QMessageBox.information(self, 'Bad Number', 'The number in '
                                            + widget.objectName()
                                            + ' appears to contain a bad value. Check that '
                                              'it contains no letters or spaces')

        self.num_checks_total_label.setText(str(num_checks))
        self.bills_total_label.setText(str('{:,.2f}'.format(float(bills_total))))
        self.coins_total_label.setText(str('{:,.2f}'.format(float(coins_total))))
        self.designated_total_label.setText(str('{:,.2f}'.format(float(special_total))))
        self.checks_total_label.setText(str('{:,.2f}'.format(float(checks_total))))

        total = bills_total + coins_total + checks_total
        self.total_total_label.setText(str('{:,.2f}'.format(float(total))))

    def rewrite_designations(self, designations):
        index = 0
        for widget in self.findChildren(QLabel, 'special_label'):
            widget.setText(designations[index])
            index += 1

    def print_rec(self):
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            # letter size = 612.0 x 792.0
            # create variables based on letter-sized canvas
            marginH = 100
            marginV = 80
            firstLine = 792 - marginV
            lastLine = marginV
            lineStart = marginH
            lineEnd = 612 - marginH
            lineHeight = 16

            appData = os.getenv('APPDATA')
            print_file_loc = appData + '/WeeklyGiving/print.pdf'
            self.lwg.write_log('print_file_loc: ' + print_file_loc)

            currentLine = firstLine
            canvas = canvas.Canvas(print_file_loc, pagesize=letter)
            canvas.setLineWidth(1.0)
            canvas.setFont('Helvetica-Bold', 16)
            canvas.drawString(lineStart, currentLine, self.lwg.name + ' Weekly Giving Report')
            currentLine -= 5
            canvas.line(lineStart, currentLine, lineEnd, currentLine)

            currentLine -= lineHeight
            canvas.setFont('Helvetica-Bold', 11)
            canvas.drawString(lineStart, currentLine, 'Date:')
            canvas.setFont('Helvetica', 11)
            canvas.drawString(lineStart + 35, currentLine, self.date_line_edit.text())
            canvas.setFont('Helvetica-Bold', 11)
            canvas.drawString(lineStart + 120, currentLine, 'Prepared By:')
            canvas.setFont('Helvetica', 11)
            canvas.drawString(lineStart + 195, currentLine, self.prep_line_edit.text())
            canvas.drawRightString(lineEnd, currentLine, 'ID: ' + self.id_num_label.text())

            currentLine -= lineHeight
            canvas.setFont('Helvetica-Bold', 11)
            canvas.drawString(lineStart, currentLine, 'Signature:')
            currentLine -= lineHeight
            canvas.rect(lineStart, currentLine - 20, 300, 30)

            topLineofEntries = currentLine - 50
            currentLine = topLineofEntries
            rememberCurrentLine = currentLine
            canvas.drawString(lineStart, currentLine, '$100 Bills')
            currentLine -= lineHeight
            canvas.drawString(lineStart, currentLine, '$50 Bills')
            currentLine -= lineHeight
            canvas.drawString(lineStart, currentLine, '$20 Bills')
            currentLine -= lineHeight
            canvas.drawString(lineStart, currentLine, '$10 Bills')
            currentLine -= lineHeight
            canvas.drawString(lineStart, currentLine, '$5 Bills')
            currentLine -= lineHeight
            canvas.drawString(lineStart, currentLine, '$1 Bills')

            billsArray = [
                self.bills_100_line_edit.text(),
                self.bills_50_line_edit.text(),
                self.bills_20_line_edit.text(),
                self.bills_10_line_edit.text(),
                self.bills_5_line_edit.text(),
                self.bills_1_line_edit.text()
            ]

            column1 = 180
            canvas.setFont('Helvetica', 11)
            currentLine = rememberCurrentLine
            for num in billsArray:
                canvas.drawRightString(column1, currentLine, num)
                currentLine -= lineHeight

            currentLine -= lineHeight
            rememberCurrentLine = currentLine

            canvas.setFont('Helvetica-Bold', 11)
            canvas.drawString(lineStart, currentLine, '$1 Coins')
            currentLine -= lineHeight
            canvas.drawString(lineStart, currentLine, 'Quarters')
            currentLine -= lineHeight
            canvas.drawString(lineStart, currentLine, 'Dimes')
            currentLine -= lineHeight
            canvas.drawString(lineStart, currentLine, 'Nickels')
            currentLine -= lineHeight
            canvas.drawString(lineStart, currentLine, 'Pennies')
            currentLine -= lineHeight

            coinsArray = [
                self.dollar_line_edit.text(),
                self.quarter_line_edit.text(),
                self.dime_line_edit.text(),
                self.nickel_line_edit.text(),
                self.penny_line_edit.text()
            ]

            canvas.setFont('Helvetica', 11)
            currentLine = rememberCurrentLine
            for num in coinsArray:
                canvas.drawRightString(column1, currentLine, num)
                currentLine -= lineHeight

            column2 = 210
            canvas.setFont('Helvetica-Bold', 11)
            currentLine = topLineofEntries
            canvas.drawString(column2, currentLine, 'Love Offerings')
            currentLine -= lineHeight
            canvas.drawString(column2, currentLine, 'Equip Offerings')
            currentLine -= lineHeight
            canvas.drawString(column2, currentLine, 'Seminary Offerings')
            currentLine -= lineHeight
            canvas.drawString(column2, currentLine, 'Growth Offerings')
            currentLine -= lineHeight
            canvas.drawString(column2, currentLine, 'Camp Offerings')
            currentLine -= lineHeight
            canvas.drawString(column2, currentLine, 'Sunday School Offerings')
            currentLine -= lineHeight
            canvas.drawString(column2, currentLine, 'Other Designations')
            currentLine -= lineHeight

            specialArray = []
            for widget in self.findChildren(QLineEdit, 'special_edit'):
                specialArray.append(widget.text())
            column3 = 400
            canvas.setFont('Helvetica', 11)
            currentLine = topLineofEntries
            for num in specialArray:
                canvas.drawRightString(column3, currentLine, '${:,.2f}'.format(float(num)))
                currentLine -= lineHeight

            column4 = 440
            canvas.setFont('Helvetica-Bold', 11)
            currentLine = topLineofEntries + lineHeight
            canvas.drawString(column4, currentLine, 'Checks:')
            currentLine = topLineofEntries
            for i in range(1, 31):
                canvas.drawString(column4, currentLine, str(i))
                currentLine -= lineHeight

            checksArray = []
            for widget in self.findChildren(QLineEdit, QRegExp('check*')):
                checksArray.append(widget.text())

            column5 = lineEnd  # prev 500
            canvas.setFont('Helvetica', 11)
            currentLine = topLineofEntries
            for num in checksArray:
                canvas.drawRightString(column5, currentLine, '${:,.2f}'.format(float(num.replace(',', ''))))
                currentLine -= lineHeight

            currentLine = 300
            canvas.setFont('Helvetica-Bold', 12)
            canvas.drawString(lineStart + 20, currentLine, 'Total Designated Offerings:')
            currentLine -= lineHeight * 2
            canvas.drawString(lineStart + 20, currentLine, 'Total Bills:')
            currentLine -= lineHeight
            canvas.drawString(lineStart + 20, currentLine, 'Total Coins:')
            currentLine -= lineHeight
            canvas.drawString(lineStart + 20, currentLine, 'Total Checks:')
            currentLine -= lineHeight * 2
            canvas.setFont('Helvetica-BoldOblique', 14)
            canvas.drawString(lineStart + 20, currentLine, 'Total Deposit:')
            currentLine -= lineHeight * 2
            canvas.setFont('Helvetica-Bold', 12)
            canvas.drawString(lineStart + 20, currentLine, 'Number of Checks:')

            currentLine = 300
            column2 = 370
            canvas.setFont('Helvetica', 12)
            canvas.drawRightString(column2, currentLine, self.designated_total_label.text())
            currentLine -= lineHeight * 2
            canvas.drawRightString(column2, currentLine, self.bills_total_label.text())
            currentLine -= lineHeight
            canvas.drawRightString(column2, currentLine, self.coins_total_label.text())
            currentLine -= lineHeight
            canvas.drawRightString(column2, currentLine, self.checks_total_label.text())
            currentLine -= lineHeight * 2
            canvas.setFont('Helvetica-BoldOblique', 14)
            canvas.drawRightString(column2, currentLine, self.total_total_label.text())
            currentLine -= lineHeight * 2
            canvas.setFont('Helvetica', 12)
            canvas.drawRightString(column2, currentLine, self.num_checks_total_label.text())

            currentLine += lineHeight * 2
            canvas.setLineWidth(2.0)
            canvas.rect(lineStart, currentLine - 20, 390 - lineStart, 150)

            currentLine -= lineHeight * 5
            canvas.drawString(lineStart, currentLine, 'Notes:')
            currentLine -= lineHeight * 1.5
            canvas.drawString(lineStart + 20, currentLine, self.notes_edit.toPlainText().strip())
            currentLine += lineHeight * 1.5
            canvas.setLineWidth(1.0)
            canvas.rect(lineStart, currentLine - 60, lineEnd - lineStart, 55)
            canvas.save()

            print('Opening print subprocess')
            CREATE_NO_WINDOW = 0x08000000
            p = subprocess.Popen(
                [
                    'ghostscript/gsprint.exe',
                    print_file_loc,
                    '-ghostscript',
                    'ghostscript/gswin64.exe',
                    '-query'],
                creationflags=CREATE_NO_WINDOW,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            print('Capturing print subprocess sdtout & stderr')
            stdout, stderr = p.communicate()
            self.lwg.write_log('gsprint.exe stdout: ' + str(stdout))
            self.lwg.write_log('gsprint.exe stderr: ' + str(stderr))
        except Exception:
            logging.exception('')

    def refresh_combo_boxes(self):
        self.id_combo_box.blockSignals(True)
        self.date_combo_box.blockSignals(True)

        self.id_combo_box.clear()
        self.date_combo_box.clear()

        for item in self.lwg.get_ids():
            self.id_combo_box.addItem(str(item))

        for item in self.lwg.get_dates():
            self.date_combo_box.addItem(item[0], (1, item[1]))

        self.id_combo_box.blockSignals(False)
        self.date_combo_box.blockSignals(False)

    def show_help(self):
        self.help_window = QWidget()
        self.help_window.setFixedSize(1000, 800)
        window_layout = QVBoxLayout()
        self.help_window.setLayout(window_layout)
        try:
            help_widget = QWidget()
            help_widget.setMaximumSize(940, 1200)
            help_layout = QVBoxLayout()
            help_widget.setLayout(help_layout)
        except Exception:
            logging.exception('')

        title_label = QLabel('Weekly Giving Help')
        title_label.setFont(QFont("Helvetica", 22, QFont.Bold))
        help_layout.addWidget(title_label)

        separator0 = QWidget()
        separator0.setMinimumHeight(42)
        separator0.setStyleSheet('border-bottom: 2px solid black; margin-top: 20px; margin-bottom: 20px')
        help_layout.addWidget(separator0)

        toolbar_label = QLabel('Toolbar')
        toolbar_label.setFont(self.bold_font)
        help_layout.addWidget(toolbar_label)

        toolbar_image_label = QLabel()
        toolbar_pixmap = QPixmap('resources/navBar.png')
        toolbar_pixmap = toolbar_pixmap.scaledToWidth(900, Qt.SmoothTransformation)
        toolbar_image_label.setPixmap(toolbar_pixmap)
        help_layout.addWidget(toolbar_image_label)

        toolbar_text_label = QLabel()
        toolbar_text_label.setWordWrap(True)
        toolbar_text_label.setFont(self.plain_font)
        toolbar_text_label.setText(
            '<p>'
            'At the top of the screen you will see a toolbar. On the left of the bar are buttons you can use to navigate the records you create:'
            '<ul>'
            '    <li>Go to the first record</li>'
            '    <li>Go to the previous record</li>'
            '    <li>Go to the next record</li>'
            '    <li>Go to the last record</li>'
            '    <li>Create a new record</li>'
            '</ul>'
            '</p>'
            '<p>'
            '    In the center of the toolbar, you can bring up your records by ID number or by date.'
            '</p>'
            '<p>'
            '    Then, on the right-hand side, there are buttons to print the current record, create a graph of giving '
            '    between certain dates, and save the current record. This save button is only active after changes have '
            '    been made to the current record.'
            '</p>'
        )
        help_layout.addWidget(toolbar_text_label)

        separator1 = QWidget()
        separator1.setMinimumHeight(42)
        separator1.setStyleSheet('border-bottom: 2px solid black; margin-top: 20px; margin-bottom: 20px')
        help_layout.addWidget(separator1)

        file_label = QLabel('File Menu')
        file_label.setFont(self.bold_font)
        help_layout.addWidget(file_label)

        file_image_label = QLabel()
        file_pixmap = QPixmap('resources/fileMenu.png')
        file_image_label.setPixmap(file_pixmap)
        help_layout.addWidget(file_image_label)

        file_text_label = QLabel(
            'In the file menu, you will find commands to save the current record, '
            'print the current record, and exit the program.'
        )
        file_text_label.setWordWrap(True)
        file_text_label.setFont(self.plain_font)
        help_layout.addWidget(file_text_label)

        separator2 = QWidget()
        separator2.setMinimumHeight(42)
        separator2.setStyleSheet('border-bottom: 2px solid black; margin-top: 20px; margin-bottom: 20px')
        help_layout.addWidget(separator2)

        tools_label = QLabel('Tools Menu')
        tools_label.setFont(self.bold_font)
        help_layout.addWidget(tools_label)

        tools_image_label = QLabel()
        tools_pixmap = QPixmap('resources/toolsMenu.png')
        tools_image_label.setPixmap(tools_pixmap)
        help_layout.addWidget(tools_image_label)

        tools_text_label = QLabel(
            'In the tools menu, you will find commands to create a new record, delete the current record, '
            'or view the log file, which may contain information about program crashes or undesired behavior.'
        )
        tools_text_label.setWordWrap(True)
        tools_text_label.setFont(self.plain_font)
        help_layout.addWidget(tools_text_label)

        separator3 = QWidget()
        separator3.setMinimumHeight(42)
        separator3.setStyleSheet('border-bottom: 2px solid black; margin-top: 20px; margin-bottom: 20px')
        help_layout.addWidget(separator3)

        settings_label = QLabel('Settings Menu')
        settings_label.setFont(self.bold_font)
        help_layout.addWidget(settings_label)

        settings_image_label = QLabel()
        settings_pixmap = QPixmap('resources/settingsMenu.png')
        settings_image_label.setPixmap(settings_pixmap)
        help_layout.addWidget(settings_image_label)

        settings_text_label = QLabel(
            'In the settings menu, you will find commands to change the name that appears in the program and on your '
            'printed report, change the names of the special offering designations, change the number of checks that '
            'appears in the Checks section of your records, and to save the file that stores all your records to a '
            'different location. Note that there is currently no way to change the number of special offering '
            'designations, that number being fixed at seven.'
        )
        settings_text_label.setWordWrap(True)
        settings_text_label.setFont(self.plain_font)
        help_layout.addWidget(settings_text_label)

        scroll_area = QScrollArea()
        scroll_area.setWidget(help_widget)
        window_layout.addWidget(scroll_area)

        self.help_window.show()

    def show_about(self):
        self.about_widget = QWidget()
        about_layout = QVBoxLayout()
        self.about_widget.setLayout(about_layout)

        about_text = QTextBrowser()
        about_text.setHtml(
            'Weekly Giving is free software: you can redistribute it and/or modify it under the terms of the '
            'GNU General Public License (GNU GPL) published by the Free Software Foundation, either version 3 of the '
            'License, or (at your option) any later version.<br><br>'
            'This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the '
            'implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public '
            'License for more details.<br><br>'
            'You should have received a copy of the GNU General Public License along with this program.  If not, see '
            '<a href="http://www.gnu.org/licenses/">http://www.gnu.org/licenses/</a>.<br><br>'
            'The Weekly Giving program includes Artifex Software\'s GhostScript, licensed under the GNU Affero '
            'General Public License (GNU AGPL). See <a href="https://www.ghostscript.com/licensing/index.html">'
            'https://www.ghostscript.com/licensing/index.html</a> for more information.<br><br>'
            'This program is a work-in-progress by a guy who is not, in no way, a professional programmer. If you run '
            'into any problems, unexpected behavior, missing features, or attempts to assimilate your unique biological '
            'and technological distinctiveness, email <a href="mailto:pastorjeremywilson@gmail.com">'
            'pastorjeremywilson@gmail.com</a>'
        )
        about_text.setFont(self.plain_font)
        about_text.setMinimumSize(600, 400)
        about_layout.addWidget(about_text)
        self.about_widget.show()

class CustomDateLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()

    def focusOutEvent(self, evt):
        date = self.text().strip()
        if date == '':
            date = '1970-01-01'
            self.setText(date)
        try:
            new_date = parse(date).strftime('%Y-%m-%d')
            self.setText(new_date)
            self.setStyleSheet('color: black')
            self.setToolTip('')
            super(CustomDateLineEdit, self).focusOutEvent(evt)
        except ParserError:
            self.setStyleSheet('color: red')
            self.setToolTip('Bad date format. Try YYYY-MM-DD.')
            super(CustomDateLineEdit, self).focusOutEvent(evt)

class CustomCurrencyLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignRight)
        self.setMaximumWidth(150)
        self.setStyleSheet('background-color: white')

    def focusOutEvent(self, evt):
        amount = self.text().strip()
        if amount == '':
            amount = '0.00'
            self.setText('0.00')
        try:
            new_amount = '{:,.2f}'.format(float(amount))
            self.setText(new_amount)
            self.setStyleSheet('color: black')
            self.setToolTip('')
            super(CustomCurrencyLineEdit, self).focusOutEvent(evt)
        except ValueError:
            self.setStyleSheet('color: red')
            self.setToolTip('Bad number')
            super(CustomCurrencyLineEdit, self).focusOutEvent(evt)

class CustomIntegerLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignRight)
        self.setMaximumWidth(100)
        self.setStyleSheet('background-color: white')

    def focusOutEvent(self, evt):
        number = self.text().strip()
        if number == '':
            number = '0'
            self.setText('0')
        try:
            new_amount = int(number)
            self.setText(str(new_amount))
            self.setStyleSheet('color: black')
            self.setToolTip('')
            super(CustomIntegerLineEdit, self).focusOutEvent(evt)
        except ValueError:
            self.setStyleSheet('color: red')
            self.setToolTip('Bad number')
            super(CustomIntegerLineEdit, self).focusOutEvent(evt)
