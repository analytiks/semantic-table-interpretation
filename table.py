from dateutil.parser import parse
import pandas as pd


class TableEntity(object):
    """Abstract class for all the table element classes(Table class, 
    Column class, Row class, Cell class)
    DO NOT DIRECLY CHANGE PRIVATE VARIABLES - All the required methods are provided
    """

    def __init__(self):
        self.__predicted_labels__ = []
        self.__true_label__ = None

    def add_predicted_label(self, label):
        """Appends given label to predicted labels list.
        Args:
            label: label to be added
        """
        self.predicted_labels.append(label)

    def get_predicted_labels(self):
        return self.predicted_labels
    
    def set_predicted_labels(self, labels):
        if(isinstance(labels,list)):
            self.__predicted_labels__ = labels
    
    def get_true_label(self):
        return self.__true_label__

    def set_true_label(self, label):
        self.__predicted_labels__ = label

    def evaluate_mapping(self):
        """Check if the predicted mapping is correct.
        Returns:
            Boolean: True if mapping is corrrect. False otherwise
        """
        if(self.__true_label__==self.__predicted_labels__[0]):
            return True
        else:
            return False

class Table(TableEntity):

    def __init__(self):
        self.__cols__ = []
        self.__rows__ = []

    def set_columns(self, cols):
        self.__cols__ = cols

    def set_columns(self, rows):
        self.__rows__ = rows

    def get_columns(self):
        return self.__cols__

    def get_rows(self):
        return self.__rows__

    def get_NE_cols(self):
        col_indices = []
        i = 0
        for column in self.__cols__:
            if(column.is_NE()):
                col_indices.append(i)
            i += 1
        sub_table = self.get_subtable(col_indices, "col")
        return sub_table
    
    def get_numeric_cols(self):
        col_indices = []
        i = 0
        for column in self.__cols__:
            if(column.is_numeric()):
                col_indices.append(i)
            i += 1
        sub_table = self.get_subtable(col_indices, "col")
        return sub_table

    def get_date_cols(self):
        col_indices = []
        i = 0
        for column in self.__cols__:
            if(column.is_date()):
                col_indices.append(i)
            i += 1
        sub_table = self.get_subtable(col_indices, "col")
        return sub_table

    def parse_csv(self, file_path):
        temp_df = pd.read_csv(file_path)
        headers = temp_df.dtypes.index
        for header in headers:
            values = temp_df[[header]].values
            cells = []
            for value in values:
                cells.append(Cell(value[0]))
            self.__cols__.append(Column(header, cells))
        row_list = temp_df.values.tolist()
        for row in row_list:
            cells = []
            for value in row:
                cells.append(Cell(value))
            self.__rows__.append(Row(cells))

    def get_subtable(self, indices=[], axis="col"):
        new_cols = []
        new_rows = []
        indices.sort()
        if(axis == "col"):
            for i in indices:
                new_cols.append(self.__cols__[i])
            for row in self.__rows__:
                row_cells = []
                for j in indices:
                    row_cells.append(row.get_cells()[j])
                new_rows.append(Row(row_cells))
        sub_table = Table()
        sub_table.__cols__ = new_cols
        sub_table.__rows__ = new_rows
        return sub_table

    def visualize(self):
        table_content = "<tr>"
        for col in self.__cols__:
            th_title = "title='True Concept:{} \
                        &#xA;Predicted Concepts:".format(col.get_true_label())
            for label in col.__predicted_labels__:
                th_title = "\n" + th_title+label[0]+"\n"
            th_title = th_title + "'"
            curr_header = "<th {}>{}</th>".format(th_title, col.get_header())
            table_content = table_content + curr_header
        table_content = table_content + "</tr>"

        for row in self.__rows__:
            table_content = table_content + row.visualize()
        html = "<!DOCTYPE html><html>\
                <head><meta charset=\"UTF-8\">\
                <link rel='stylesheet'\
                 href='https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css'\
                 integrity='sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm'\
                 crossorigin='anonymous'>\
                <title>Table visualizer</title></head>\
                <body>\
                <div class='container'>\
                <div class='row' style='padding-top:60px'>\
                <table class='table'>{}</table>\
                </div></div></body>\
                </html>".format(table_content)

        with open("output.html", 'wb') as f:
            f.write(html)



class Column(TableEntity):

    def __init__(self, header, cells):
        super(Column, self).__init__()
        self.__header__ = header
        self.__cells__ = cells
        self.numeric_col = None
        self.date_col = None
        self.NE_col = None
    
    def get_header(self):
        return self.__header__

    def set_cells(self, cells):
        self.__cells__ = cells
    
    def get_cells(self):
        return self.__cells__

    def is_NE(self):
        if(self.NE_col is None):
            NE_count = 0
            for cell in self.__cells__:
                if(cell.is_NE()):
                    NE_count += 1
            ne_percentage = float(NE_count)/float(len(self.__cells__))
            if(ne_percentage > 0.8):
                self.NE_col = True
            else:
                self.NE_col = False
        return self.NE_col

    def is_numeric(self):
        if(self.numeric_col is None):
            numeric_count = 0
            for cell in self.__cells__:
                if(cell.is_numeric()):
                    numeric_count += 1
            numeric_percentage = float(numeric_count)/len(self.__cells__)
            if(numeric_percentage > 0.8):
                self.numeric_col = True
            else:
                self.numeric_col = False
        return self.numeric_col

    def is_date(self):
        if(self.date_col is None):
            date_count = 0
            for cell in self.__cells__:
                if(cell.is_date()):
                    date_count += 1
            date_percentage = float(date_count)/float(len(self.__cells__))
            if(date_percentage > 0.8):
                self.date_col = True
            else:
                self.date_col = False
        return self.date_col
    
    def get_cardinality(self):
        temp_values = []
        for cell in self.__cells__:
            temp_values.append(cell.get_value())
        return len(set(temp_values))


class Row(TableEntity):

    def __init__(self, cells):
        super(Row, self).__init__()
        self.__cells__ = cells
    
    def set_cells(self, cells):
        self.__cells__ = cells
    
    def get_cells(self):
        return self.__cells__

    def visualize(self):
        html = "<tr>"
        for cell in self.__cells__:
            html = html + cell.visualize()
        html = html + "</tr>"
        return html


class Cell(TableEntity):

    def __init__(self, value):
        super(Cell, self).__init__()
        self.__value__ = value
    
    def set_value(self, value):
        self.__value__ = value
    
    def get_value(self):
        return self.__value__

    def is_NE(self):
        if(self.is_date()):
            return False
        elif(self.is_numeric()):
            return False
        else:
            return True

    def is_numeric(self):
        try:
            float(self.__value__)
            return True
        except ValueError:
            return False

    def is_date(self):
        try:
            parse(self.__value__)
            return True
        except ValueError:
            return False
        except TypeError:
            return False

    def visualize(self):
        html_actual = "<td title=\"Actual concept: {}".format(self.get_true_label())
        html_predicted = "&#xA;Predicted concepts: "
        html_value = "\">{}</td>".format(self.__value__)
        for label in self.__predicted_labels__:
            html_predicted = html_predicted + label
        html = html_actual+html_predicted+html_value
        return html


if __name__ == "__main__":
    test_table = Table()
    test_table.parse_csv('sample.csv')
    ne_table = test_table
    for col in ne_table.__cols__:
        print col.get_header() + ": ",
        print col.get_cardinality()
    test_table.visualize()