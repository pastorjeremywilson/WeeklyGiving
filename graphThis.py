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

import datetime

import matplotlib.pyplot as plot


class LineGraph:
    def __init__(self, pairs):
        self.x = []
        self.y = []
        for item in pairs:
            self.x.append(item[0])
            self.y.append(item[1])

    def graph_values_by_date_line(self):
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
