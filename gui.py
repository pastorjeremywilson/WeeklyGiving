import json
import logging
import os

from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from dateutil.parser import parse, ParserError
from PyQt6.QtCore import QRegularExpression, Qt, pyqtSignal, QSize, QRectF
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter, QPageSize, QPageLayout
from PyQt6.QtWidgets import QMainWindow, QWidget, QGridLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QLineEdit, \
    QTextEdit, QVBoxLayout, QScrollArea, QMessageBox, QTextBrowser, QApplication


class GUI(QMainWindow):
    create_gui = pyqtSignal()
    set_total_labels = pyqtSignal(list)
    changes = None
    main_title_label = None
    all_values = None

    plain_font = QFont('Helvetica', 11)
    standard_font = plain_font
    bold_font = QFont('Helvetica', 11, QFont.Weight.Bold)
    title_font = QFont('Helvetica', 16, QFont.Weight.Bold)
    light_green = '#eaffe8'
    dark_green = '#00641e'

    def __init__(self, lwg, name, num_checks=30):
        """
        :param WeeklyGiving lwg: WeeklyGiving instance
        :param str name: Church name from config
        :param int num_checks: Number of checks to display
        """
        self.lwg = lwg
        self.name = name
        self.num_checks = num_checks

        super().__init__()
        self.create_gui.connect(self.init_components)
        self.set_total_labels.connect(self.set_totals)

    def closeEvent(self, event):
        """
        @override
        Checks changes and prompts for user input before closing
        """
        event.ignore()
        if self.changes:
            result = QMessageBox.question(
                self,
                'Changes Detected',
                'Changes have been made. Save before Closing?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)

            if result == QMessageBox.StandardButton.Yes:
                self.lwg.save_rec()
                self.lwg.do_backup()
                event.accept()
            elif result == QMessageBox.StandardButton.No:
                self.lwg.do_backup()
                event.accept()
            else:
                event.ignore()
        else:
            self.lwg.do_backup()
            event.accept()

    def init_components(self):
        """
        Creates the gui components and lays them out
        """
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

        self.name_widget = QWidget()
        name_layout = QHBoxLayout()
        self.name_widget.setLayout(name_layout)

        self.main_title_label = QLabel(self.lwg.name + ' Weekly Giving Report')
        self.main_title_label.setFont(self.title_font)
        self.main_title_label.setStyleSheet('color: white')
        name_layout.addWidget(self.main_title_label)

        name_change_button = QPushButton()
        name_change_button.setIcon(QIcon('./resources/edit_icon_white.svg'))
        name_change_button.setToolTip('Change Church Name')
        name_change_button.setIconSize(QSize(20, 20))
        name_change_button.setFixedSize(20, 20)
        name_change_button.setStyleSheet(
            'QPushButton {'
            '   border: none;'
            '}'
            'QPushButton:ToolTip {'
            '   background: white;'
            '}'
        )
        name_change_button.pressed.connect(self.change_name)
        name_layout.addWidget(name_change_button)
        name_layout.addStretch()

        self.main_layout.addWidget(self.name_widget, 0, 0)

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
        """
        Method to create the gui's menu bar
        """
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('File')

        save_action = file_menu.addAction('Save Record')
        save_action.triggered.connect(self.lwg.save_rec)

        print_action = file_menu.addAction('Print')
        print_action.triggered.connect(self.print_pdf)

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

        include_action = config_menu.addAction('Include Special Designations in Total Deposit')
        include_action.setCheckable(True)
        if self.lwg.include_special_in_total:
            include_action.setChecked(True)
        else:
            include_action.setChecked(False)
        include_action.triggered.connect(self.include_special)

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
        """
        Method to create the gui's top (button) widget
        """
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
        print_rec_button.pressed.connect(self.print_pdf)
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

        self.showMaximized()
        self.changes = False
        self.save_button.setEnabled(False)

    def build_info_frame(self):
        """
        Method to build the widget containing important record info
        """
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
        """
        Method to create the widget containing the bills fields
        """
        self.bills_widget = QWidget()
        self.bills_widget.setStyleSheet('background-color: ' + self.light_green)

        bills_layout = QGridLayout()
        self.bills_widget.setLayout(bills_layout)

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

        self.main_layout.addWidget(self.bills_widget, 3, 0)

    def build_coins_frame(self):
        """
        Method to create the gui's coins fields
        """
        self.coins_widget = QWidget()
        self.coins_widget.setStyleSheet('background-color: ' + self.light_green)

        coins_layout = QGridLayout()
        self.coins_widget.setLayout(coins_layout)

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

        self.main_layout.addWidget(self.coins_widget, 4, 0)

    def build_special_frame(self):
        """
        Method to create the gui's special designation fields
        """
        self.special_widget = QWidget()
        self.special_widget.setStyleSheet('background-color: ' + self.light_green)

        special_layout = QVBoxLayout()
        self.special_widget.setLayout(special_layout)

        special_label = QLabel('Special Designations')
        special_label.setStyleSheet('color: ' + self.dark_green)
        special_label.setFont(self.bold_font)
        special_label.setMinimumHeight(30)
        special_layout.addWidget(special_label)

        for i in range(0, len(self.lwg.spec_designations)):
            special_line_widget = QWidget()
            special_line_layout = QHBoxLayout()
            special_line_widget.setLayout(special_line_layout)

            push_button = QPushButton()
            push_button.setObjectName('special_label' + str(i))
            push_button.setIcon(QIcon('./resources/edit_icon_black.svg'))
            push_button.setToolTip('Change Special Designation Name')
            push_button.setIconSize(QSize(12, 12))
            push_button.setFixedSize(12, 12)
            push_button.setStyleSheet('border: none;')
            push_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            push_button.pressed.connect(self.change_name)
            special_line_layout.addWidget(push_button)

            label = QLabel(self.lwg.column_pairs[i][1])
            label.setObjectName('special_label' + str(i))
            label.setFont(self.plain_font)
            special_line_layout.addWidget(label)
            special_line_layout.addStretch()

            line_edit = CustomCurrencyLineEdit()
            line_edit.setFont(self.plain_font)
            line_edit.setObjectName('special_edit' + str(i))
            line_edit.setText('0.00')
            line_edit.textEdited.connect(self.on_change)
            special_line_layout.addWidget(line_edit)

            special_layout.addWidget(special_line_widget)

        self.main_layout.addWidget(self.special_widget, 3, 2, 2, 1)

    def build_checks_frame(self):
        """
        Method to create the gui's checks fields
        """
        self.checks_widget = QWidget()
        self.checks_widget.setStyleSheet('background-color: ' + self.light_green)

        checks_layout = QGridLayout()
        self.checks_widget.setLayout(checks_layout)

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
        scroll_container.setWidget(self.checks_widget)

        self.main_layout.addWidget(scroll_container, 3, 1, 3, 1)

    def build_notes_frame(self):
        """
        Method to create the notes area of the gui
        """
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
        """
        Method to create the totals area of the gui
        """
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
        num_checks_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_layout.addWidget(num_checks_label, 1, 0)

        self.num_checks_total_label = QLabel()
        self.num_checks_total_label.setFont(self.plain_font)
        self.num_checks_total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_layout.addWidget(self.num_checks_total_label, 1, 1)

        designated_label = QLabel('Total Designated Offerings:')
        designated_label.setFont(self.bold_font)
        designated_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_layout.addWidget(designated_label, 2, 0)

        self.designated_total_label = QLabel()
        self.designated_total_label.setFont(self.plain_font)
        self.designated_total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_layout.addWidget(self.designated_total_label, 2, 1)

        bills_label = QLabel('Total Bills:')
        bills_label.setFont(self.bold_font)
        bills_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_layout.addWidget(bills_label, 4, 0)

        self.bills_total_label = QLabel()
        self.bills_total_label.setFont(self.plain_font)
        self.bills_total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_layout.addWidget(self.bills_total_label, 4, 1)

        coins_label = QLabel('Total Coins:')
        coins_label.setFont(self.bold_font)
        coins_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_layout.addWidget(coins_label, 5, 0)

        self.coins_total_label = QLabel()
        self.coins_total_label.setFont(self.plain_font)
        self.coins_total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_layout.addWidget(self.coins_total_label, 5, 1)

        checks_label = QLabel('Total Checks:')
        checks_label.setFont(self.bold_font)
        checks_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_layout.addWidget(checks_label, 6, 0)

        self.checks_total_label = QLabel()
        self.checks_total_label.setFont(self.plain_font)
        self.checks_total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_layout.addWidget(self.checks_total_label, 6, 1)

        total_label = QLabel('Total:')
        total_label.setFont(self.bold_font)
        total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_layout.addWidget(total_label, 8, 0)

        self.total_total_label = QLabel()
        self.total_total_label.setFont(self.bold_font)
        self.total_total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_layout.addWidget(self.total_total_label, 8, 1)

        self.main_layout.addWidget(totals_widget, 4, 3)

    def change_name(self):
        """
        Method that creates a QLineEdit that overlays a chosen label the user wants to change. Passes to
        complete_change_name in order to apply the user's changes.
        """
        sender = self.sender()
        sender.setEnabled(False)
        widget = self.findChild(QLabel, sender.objectName())

        if 'special_label' in widget.objectName():
            widget_text = widget.text()
            checkmark_icon = './resources/checkmark_black.svg'

            biggest_width = 0
            for label in self.special_widget.findChildren(QLabel, QRegularExpression('special_label*')):
                if label.width() > biggest_width:
                    biggest_width = label.width()

        else:
            widget_text = widget.text().replace(' Weekly Giving Report', '')
            checkmark_icon = './resources/checkmark_white.svg'
            biggest_width = widget.width()

        name_change_line_edit = QLineEdit(widget_text)
        name_change_line_edit.setParent(widget.parent())
        name_change_line_edit.setFixedSize(biggest_width, widget.height())
        name_change_line_edit.setFont(widget.font())
        name_change_line_edit.setStyleSheet('background: white; color: black;')
        name_change_line_edit.move(widget.pos())
        name_change_line_edit.show()

        name_change_push_button = QPushButton()
        name_change_push_button.setIcon(QIcon(checkmark_icon))
        name_change_push_button.setIconSize(QSize(widget.height(), widget.height()))
        name_change_push_button.setFixedSize(widget.height() + 5, widget.height() + 5)
        name_change_push_button.setStyleSheet('border: none;')
        name_change_push_button.setParent(widget.parent())
        name_change_push_button.pressed.connect(
            lambda: self.complete_name_change(name_change_line_edit, name_change_push_button, widget, sender))
        name_change_push_button.move(
            name_change_line_edit.pos().x() + name_change_line_edit.width(), name_change_line_edit.pos().y())
        name_change_push_button.show()

        name_change_line_edit.setFocus()
        name_change_line_edit.selectAll()
        name_change_line_edit.returnPressed.connect(
            lambda: self.complete_name_change(name_change_line_edit, name_change_push_button, widget, sender))

    def complete_name_change(self, line_edit, push_button, widget, sender):
        """
        Method to apply the user's changes to editable labels. Removes the QLineEdit and QPushButton overlays,
        writes the changes to the config file, and changes the chosen label.
        :param QLineEdit line_edit: the line edit created by change_name
        :param QPushButton push_button: the push_button created by change_name
        :param QLabel widget: the label being changed
        :param QWidget sender: the sender that initiated change_name
        """
        line_edit.hide()
        line_edit.deleteLater()
        push_button.hide()
        push_button.deleteLater()

        sender.setEnabled(True)

        try:
            with open(self.lwg.config_file_loc, 'r') as file:
                config_json = json.loads(file.read())

            if 'special_label' in widget.objectName():
                num = widget.objectName()[len(widget.objectName()) - 1]
                key = 'spec' + str(int(num) + 1)

                config_json['specialDesignations'][key] = line_edit.text()
                widget.setText(line_edit.text())

                for i in range(len(self.lwg.column_pairs)):
                    if self.lwg.column_pairs[i][0] == key:
                        self.lwg.column_pairs[i][1] = line_edit.text()
            else:
                self.lwg.name = line_edit.text()

                config_json['name'] = line_edit.text()
                widget.setText(line_edit.text() + ' Weekly Giving Report')

            with open(self.lwg.config_file_loc, 'w') as file:
                file.write(json.dumps(config_json))

            self.main_title_label.setText(self.lwg.name + ' Weekly Giving Report')

        except OSError as err:
            self.lwg.write_log('*Critical error in WeeklyGiving.change_name: ' + str(err))

    def include_special(self):
        """
        Method called when user changes the 'include special designations in totals' menu action
        """
        sender = self.sender()
        self.lwg.include_special(sender)

        self.on_change(False)

    def on_change(self, change_state=True):
        """
        Method to recalculate totals, set changes variable to true, and enable the save button if changes are made
        to any of the QLineEdits.
        :param bool change_state: optional: send False if changes to data have not been made
        """
        all_values = []
        for line_edit in self.bills_widget.findChildren(QLineEdit):
            all_values.append(line_edit.text())
        for line_edit in self.coins_widget.findChildren(QLineEdit):
            all_values.append(line_edit.text())
        for line_edit in self.special_widget.findChildren(QLineEdit):
            all_values.append(line_edit.text())
        for line_edit in self.checks_widget.findChildren(QLineEdit):
            all_values.append(line_edit.text())

        if change_state:
            self.changes = True
            self.save_button.setEnabled(True)

        from weekly_giving import Recalc
        recalc = Recalc(all_values, self)
        self.lwg.thread_pool.start(recalc)

    def fill_values(self, result_dictionary):
        """
        Method to take data stored in a dictionary and use it to populate the appropriate line edits in the gui
        :param dict result_dictionary: All data from the record to be displayed
        """
        self.clear_all_values()

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

            #clear checks and special offering boxes
            for widget in self.findChildren(QLineEdit, QRegularExpression('special_edit*')):
                widget.setText('')
            for i in range(0, self.lwg.max_checks):
                self.findChild(QLineEdit, 'checks_' + str(i)).setText('')

            specials = []
            for key in result_dictionary:
                if 'spec' in key:
                    specials.append(result_dictionary[key])

            index = 0
            for widget in self.findChildren(QLineEdit, QRegularExpression('special_edit*')):
                if len(specials[index]) > 0:
                    value = float(specials[index].replace(',', ''))
                    if value > 0:
                        widget.setText(str('{:,.2f}'.format(value)))
                        index += 1

            for key in result_dictionary:
                if 'check' in key and not 'quantity' in key and not 'tot' in key and len(result_dictionary[key]) > 0:
                    value = float(result_dictionary[key].replace(',', ''))
                    if value > 0:
                        self.findChild(QLineEdit, key).setText(str('{:,.2f}'.format(value)))

            notes = result_dictionary['notes']
            notes = notes.replace('<apost>', '\'')
            notes = notes.replace('<quot>', '\"')
            self.notes_edit.setPlainText(notes)

            self.num_checks_total_label.setText(str(result_dictionary['quantity_of_checks']))

            self.changes = False
        except Exception:
            logging.exception('')

    def set_totals(self, totals):
        """
        Method to change the totals labels to the amounts calculated in weekly_giving.Recalc
        :param list totals: list of totals to be displayed
        """
        self.num_checks_total_label.setText(str(totals[4]))
        self.bills_total_label.setText(str('{:,.2f}'.format(totals[0])))
        self.coins_total_label.setText(str('{:,.2f}'.format(totals[1])))
        self.designated_total_label.setText(str('{:,.2f}'.format(totals[2])))
        self.checks_total_label.setText(str('{:,.2f}'.format(totals[3])))

        if self.lwg.include_special_in_total:
            total = totals[0] + totals[1] + totals[2] + totals[3]
        else:
            total = totals[0] + totals[1] + totals[3]
        self.total_total_label.setText(str('{:,.2f}'.format(float(total))))
        QApplication.processEvents()

    def clear_all_values(self):
        for widget in self.findChildren(QLineEdit):
            widget.setText('')
        self.notes_edit.setText('')

    def rewrite_designations(self, designations):
        """
        Method to iterate the user's changed special designation labels and change them in the gui
        """
        index = 0
        for widget in self.findChildren(QLabel, QRegularExpression('special_label*')):
            widget.setText(designations[index])
            QApplication.processEvents()
            index += 1

    def make_pdf(self):
        """
        Method to format and print the record data currently being displayed. Uses reportlab to create a PDF, which
        will then be printed.
        """

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
        canvas.drawString(column2, currentLine, self.lwg.spec_designations['spec1'])
        currentLine -= lineHeight
        canvas.drawString(column2, currentLine, self.lwg.spec_designations['spec2'])
        currentLine -= lineHeight
        canvas.drawString(column2, currentLine, self.lwg.spec_designations['spec3'])
        currentLine -= lineHeight
        canvas.drawString(column2, currentLine, self.lwg.spec_designations['spec4'])
        currentLine -= lineHeight
        canvas.drawString(column2, currentLine, self.lwg.spec_designations['spec5'])
        currentLine -= lineHeight
        canvas.drawString(column2, currentLine, self.lwg.spec_designations['spec6'])
        currentLine -= lineHeight
        canvas.drawString(column2, currentLine, self.lwg.spec_designations['spec7'])
        currentLine -= lineHeight

        specialArray = []
        for widget in self.findChildren(QLineEdit, QRegularExpression('special_edit*')):
            specialArray.append(widget.text())
        column3 = 400
        canvas.setFont('Helvetica', 11)
        currentLine = topLineofEntries
        for num in specialArray:
            if len(num) > 0:
                value = float(num.replace(',', ''))
                if value > 0:
                    canvas.drawRightString(column3, currentLine, '${:,.2f}'.format(value))
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
        for widget in self.findChildren(QLineEdit, QRegularExpression('check*')):
            checksArray.append(widget.text())

        column5 = lineEnd  # prev 500
        canvas.setFont('Helvetica', 11)
        currentLine = topLineofEntries
        for num in checksArray:
            if len(num) > 0:
                value = float(num.replace(',', ''))
                if value > 0:
                    canvas.drawRightString(column5, currentLine, '${:,.2f}'.format(value))
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

        try:
            canvas.save()

            return print_file_loc

        except Exception as ex:
            self.lwg.write_log('*Error during printing: ' + str(ex))

    def print_pdf(self):
        popup = Popup(self, 'Preparing Printout...')
        popup.show()
        QApplication.processEvents()

        pdf_doc = QPdfDocument(self)
        pdf_doc.load(self.make_pdf())

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setDocName('Weekly Giving Report')
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)

        print_dialog = QPrintDialog(printer)
        painter = QPainter(print_dialog)
        painter.drawImage(QRectF(0, 0, 1100, 850), pdf_doc.render(0, QSize(1100, 850)))

        popup.deleteLater()
        result = print_dialog.exec()

        if result == QPrintDialog.DialogCode.Accepted:
            self.do_print(pdf_doc, printer)

    def do_print(self, pdf_doc, printer):
        range_list = printer.pageRanges().toRangeList()
        pages_to_print = []
        if len(range_list) > 0:
            for i in range(len(range_list)):
                for j in range(range_list[i].from_, range_list[i].to + 1):
                    pages_to_print.append(j - 1)
        else:
            for i in range(pdf_doc.pageCount()):
                pages_to_print.append(i)

        page_rect_inch = printer.pageRect(QPrinter.Unit.Inch)
        dpi_x = printer.physicalDpiX()
        dpi_y = printer.physicalDpiY()
        rect = QRectF(
            0,
            0,
            page_rect_inch.width() * dpi_x,
            page_rect_inch.height() * dpi_y
        )
        painter = QPainter(printer)
        painter.begin(printer)
        do_new_page = False
        for page in pages_to_print:
            if do_new_page:
                printer.newPage()
            render = pdf_doc.render(page, QSize(int(rect.width()), int(rect.height())))
            painter.drawImage(rect, render)
            do_new_page = True
        painter.end()

    def refresh_combo_boxes(self):
        """
        Method to repopulate the id and date comboboxes when records are added, removed, or altered
        """
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
        """
        Method to create and display the help window
        """
        self.help_window = QWidget()
        self.help_window.setFixedSize(1000, 800)
        window_layout = QVBoxLayout()
        self.help_window.setLayout(window_layout)
        
        help_widget = QWidget()
        help_widget.setMaximumSize(940, 1200)
        help_layout = QVBoxLayout()
        help_widget.setLayout(help_layout)

        title_label = QLabel('Weekly Giving Help')
        title_label.setFont(QFont("Helvetica", 22, QFont.Weight.Bold))
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
        toolbar_pixmap = toolbar_pixmap.scaledToWidth(900, Qt.TransformationMode.SmoothTransformation)
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
            '<p>'
            '    Also note that any label in the program that has an edit icon can be edited to suit your needs.'
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
            'In the file menu, you will find commands to <strong>save</strong> the current record, '
            '<strong>print</strong> the current record, and <strong>exit</strong> the program.'
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
            'In the tools menu, you will find commands to <strong>create a new record</strong>, <strong>delete</strong> the current record, '
            'or <strong>view the log file</strong>, which may contain information about program crashes or undesired behavior.'
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
            'In the settings menu, you will find commands to <strong>change the church name</strong> that appears in '
            'the program and on your printed report, change the names of the <strong>special offering designations'
            '</strong>, change the <strong>number of checks</strong> that appears in the Checks section of your '
            'records, choose whether <strong>special designations</strong> should be included in the <strong>total '
            'deposit</strong>, and to save the file that stores all your records to a <strong>different location'
            '</strong>. Note that there is currently no way to change the number of special offering designations, '
            'that number being fixed at seven.'
        )
        settings_text_label.setWordWrap(True)
        settings_text_label.setFont(self.plain_font)
        help_layout.addWidget(settings_text_label)

        scroll_area = QScrollArea()
        scroll_area.setWidget(help_widget)
        window_layout.addWidget(scroll_area)

        self.help_window.show()

    def show_about(self):
        """
        Method to create and display the about window
        """
        self.about_widget = QWidget()
        about_layout = QVBoxLayout()
        self.about_widget.setLayout(about_layout)

        about_text = QTextBrowser()
        about_text.setOpenExternalLinks(True)
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
    """
    Class implementing QLineEdit which overrides focusOutEvent, allowing for automatic formatting and invalid input
    checking of the user's input in the date field
    """
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
            self.setStyleSheet('color: black; background: white;')
            self.setToolTip('')
            super(CustomDateLineEdit, self).focusOutEvent(evt)
        except ParserError:
            self.setStyleSheet('color: red; background: white;')
            self.setToolTip('Bad date format. Try YYYY-MM-DD.')
            super(CustomDateLineEdit, self).focusOutEvent(evt)


class CustomCurrencyLineEdit(QLineEdit):
    """
    Class implementing QLineEdit which overrides focusOutEvent, allowing for automatic formatting and invalid input
    checking of the user's input in fields meant for currency
    """
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.setMaximumWidth(150)
        self.setStyleSheet('background: white')

    def focusOutEvent(self, evt):
        amount = self.text().strip().replace(',', '')
        if amount == '':
            amount = '0.00'
            self.setText('0.00')
        try:
            new_amount = '{:,.2f}'.format(float(amount))
            self.setText(new_amount)
            self.setStyleSheet('color: black; background: white;')
            self.setToolTip('')
            super(CustomCurrencyLineEdit, self).focusOutEvent(evt)
        except ValueError:
            self.setStyleSheet('color: red; background: white;')
            self.setToolTip('Bad number')
            super(CustomCurrencyLineEdit, self).focusOutEvent(evt)


class CustomIntegerLineEdit(QLineEdit):
    """
    Class implementing QLineEdit which overrides focusOutEvent, allowing for automatic formatting and invalid input
    checking of the user's input in fields meant for integers (Bills and Coins)
    """
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.setMaximumWidth(100)
        self.setStyleSheet('background: white')

    def focusOutEvent(self, evt):
        number = self.text().strip()
        if number == '':
            number = '0'
            self.setText('0')
        try:
            new_amount = int(number)
            self.setText(str(new_amount))
            self.setStyleSheet('color: black; background: white;')
            self.setToolTip('')
            super(CustomIntegerLineEdit, self).focusOutEvent(evt)
        except ValueError:
            self.setStyleSheet('color: red; background: white;')
            self.setToolTip('Bad number')
            super(CustomIntegerLineEdit, self).focusOutEvent(evt)


class Popup(QWidget):
    def __init__(self, gui, message):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setAutoFillBackground(True)
        self.setStyleSheet(f'background: {gui.dark_green}')
        layout = QVBoxLayout(self)

        label = QLabel(message)
        label.setContentsMargins(20, 10, 20, 10)
        label.setStyleSheet(f'background: {gui.dark_green}; color: white; border: 3px solid white;')
        label.setFont(gui.title_font)
        layout.addWidget(label)

        self.adjustSize()
        self.move(int(gui.width() / 2) - int(self.width() / 2), int(gui.height() / 2) - int(self.height() / 2))

