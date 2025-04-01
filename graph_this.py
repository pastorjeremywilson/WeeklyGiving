import datetime

import matplotlib.pyplot as plot
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget, QApplication


class LineGraph:
    """
    Class to create line or bar graphs of data collected when the user chooses a date range to graph
    """
    pairs = None
    def __init__(self):
        self.x = []
        self.y = []

    def graph_values_by_date_line(self):
        for item in self.pairs:
            self.x.append(item[0])
            self.y.append(item[1])

        x_vals = []
        y_vals = []
        total = 0.0
        for i in range(0, len(self.x)):
            if self.y[i]:
                clean_y = float(self.y[i].replace('$', '').replace(',', ''))
                if clean_y and self.x[i]:
                    x_vals.append(self.x[i])
                    y_vals.append(clean_y)
                    total += float(clean_y)

        plot.rc('xtick', labelsize=8)
        plot.rc('ytick', labelsize=8)

        fig, ax = plot.subplots()

        ax.set_title('Giving from ' + self.x[0] + ' through ' + self.x[len(self.x) - 1] + ' | Total: $' + str('{:,.2f}'.format(total)), size=12, weight='bold')
        ax.set_xlabel('Date', size=12, style='italic')
        ax.set_ylabel('Amount', size=12, style='italic')
        ax.plot(x_vals, y_vals, linewidth=1.0, marker='o', markersize=2, label='Sunday Offerings')

        #place a different marker for non-Sundays
        for i in range(len(x_vals)):
            if not datetime.datetime.strptime(x_vals[i], '%Y-%m-%d').weekday() == 6:
                ax.plot(x_vals[i], y_vals[i], linewidth=1.0, marker='s', markersize=3, color='red', label='Special Offering')
        ax.legend()

        for i, j in zip(x_vals, y_vals):
            ax.annotate('$' + '{:,.2f}'.format(j), xy=(i, j), xytext=(5, 2), textcoords='offset points', size=8)

        plot.xticks(rotation=90)

        figManager = plot.get_current_fig_manager()
        figManager.window.showMaximized()
        plot.show()

    def graph_values_by_date_bar(self):
        for item in self.pairs:
            self.x.append(item[0])
            self.y.append(item[1])

        x_vals = []
        y_vals = []
        total = 0.0
        for i in range(0, len(self.x)):
            if self.y[i]:
                clean_y = float(self.y[i].replace('$', '').replace(',', ''))
                if clean_y and self.x[i]:
                    x_vals.append(self.x[i])
                    y_vals.append(clean_y)
                    total += float(clean_y)

        plot.rc('xtick', labelsize=8)
        plot.rc('ytick', labelsize=8)

        fig, ax = plot.subplots()

        ax.set_title('Giving from ' + self.x[0] + ' through ' + self.x[len(self.x) - 1] + ' | Total: $' + str(
            '{:,.2f}'.format(total)), size=12, weight='bold')
        ax.set_xlabel('Date', size=12, style='italic')
        ax.set_ylabel('Amount', size=12, style='italic')
        ax.bar(x_vals, y_vals, label='Sunday Offerings')

        # place a different marker for non-Sundays
        for i in range(len(x_vals)):
            if not datetime.datetime.strptime(x_vals[i], '%Y-%m-%d').weekday() == 6:
                ax.bar(x_vals[i], y_vals[i], color='red', label='Special Offering')
        ax.legend()

        for i, j in zip(x_vals, y_vals):
            ax.annotate('$' + '{:,.2f}'.format(j), xy=(i, j), xytext=(5, 2), textcoords='offset points', size=8)

        plot.xticks(rotation=90)

        figManager = plot.get_current_fig_manager()
        figManager.window.showMaximized()
        plot.show()
