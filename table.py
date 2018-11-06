from dateutil.parser import parse as date_parser
import pandas as pd
import copy

class TableEntity(object):
    """Abstract class for all the table element classes(Table class, 
    Column class, Row class, Cell class)
    """

    def __init__(self):
        self._predicted_labels = []
        self.true_label = None
    
    @property
    def predicted_labels(self):
        return self._predicted_labels

    @predicted_labels.setter
    def predicted_labels(self, new_labels):
        if(isinstance(new_labels,list)):
            self._predicted_labels = new_labels
        else:
            raise Exception("Invalid value")
    
    @predicted_labels.deleter
    def predicted_labels(self):
        del self._length

    def evaluate_mapping(self):
        """Check if the predicted mapping is correct.
        Returns:
            Boolean: True if mapping is corrrect. False otherwise
        """
        if(self.true_label==self.predicted_labels[0]):
            return True
        else:
            return False

class Table(TableEntity):

    def __init__(self):
        super(Table, self).__init__()
        self.columns = []
        self.rows = []
        self.id = id

    def get_NE_cols(self):
        col_indices = []
        i = 0
        for column in self.columns:
            if(column.is_NE()):
                col_indices.append(i)
            i += 1
        sub_table = self.get_subtable(col_indices, "col")
        return sub_table
    
    def get_numeric_cols(self):
        col_indices = []
        i = 0
        for column in self.columns:
            if(column.is_numeric()):
                col_indices.append(i)
            i += 1
        sub_table = self.get_subtable(col_indices, "col")
        return sub_table

    def get_date_cols(self):
        col_indices = []
        i = 0
        for column in self.columns:
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
            self.columns.append(Column(header, cells))
        row_list = temp_df.values.tolist()
        for row in row_list:
            cells = []
            for value in row:
                cells.append(Cell(value))
            self.rows.append(Row(cells))

    def get_subtable(self, indices=[], axis="col"):
        new_cols = []
        new_rows = []
        indices.sort()
        if(axis == "col"):
            for i in indices:
                new_cols.append(self.columns[i])
            for row in self.rows:
                row_cells = []
                for j in indices:
                    row_cells.append(row.cells[j])
                new_rows.append(Row(row_cells))
        sub_table = Table()
        sub_table.columns = new_cols
        sub_table.rows = new_rows
        return sub_table

    def visualize(self):
        predicted_label_html = ""
        for label in self.predicted_labels:
            predicted_label_html += "<li>" + label[0] + "</li>"
        predicted_label_html = "<ul>{}</ul>".format(predicted_label_html)
        table_html = "<div class='card'>\
                        <div class='card-body'>\
                        <h5 class='card-title'>Table Element</h5>\
                        <h6 class='card-subtitle mb-2 text-muted'>True Concept:</h6>\
                        <ul><li>{}</li></ul>\
                        <h6 class='card-subtitle mb-2 text-muted'>Predicted Concepts:</h6>\
                        {}</div>\
                    </div>".format(self.true_label, predicted_label_html)
        table_content = "<tr>"
        for col in self.columns:
            th_title = "title='True Concept:\n{} \
                        \nPredicted Concepts:\n".format(col.true_label)
            for label in col.predicted_labels:
                th_title = "\n" + th_title+label[0]+"\n"
            th_title = th_title + "'"
            curr_header = "<th {}>{}</th>".format(th_title, col.header)
            table_content = table_content + curr_header
        table_content = table_content + "</tr>"

        for row in self.rows:
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
                        <div class='col'>{}</div></div>\
                    <div class='row' style='padding-top:60px'>\
                        <div class='col'>\
                            <table class='table'>{}</table>\
                        </div>\
                    </div>\
                </div>\
                </body>\
                </html>".format(table_html,table_content)

        with open("output.html", 'wb') as f:
            f.write(html)



class Column(TableEntity):
    def __init__(self, header, cells):
        super(Column, self).__init__()
        self.header = header
        self.cells = cells
        self.numeric_col = None
        self.date_col = None
        self.NE_col = None
        self.is_subject_column = False
        self.candidates = set()

    def is_NE(self):
        if(self.NE_col is None):
            NE_count = 0
            for cell in self.cells:
                if(cell.is_NE()):
                    NE_count += 1
            ne_percentage = float(NE_count)/float(len(self.cells))
            if(ne_percentage > 0.8):
                self.NE_col = True
            else:
                self.NE_col = False
        return self.NE_col

    def is_numeric(self):
        if(self.numeric_col is None):
            numeric_count = 0
            for cell in self.cells:
                if(cell.is_numeric()):
                    numeric_count += 1
            numeric_percentage = float(numeric_count)/len(self.cells)
            if(numeric_percentage > 0.8):
                self.numeric_col = True
            else:
                self.numeric_col = False
        return self.numeric_col

    def is_date(self):
        if(self.date_col is None):
            date_count = 0
            for cell in self.cells:
                if(cell.is_date()):
                    date_count += 1
            date_percentage = float(date_count)/float(len(self.cells))
            if(date_percentage > 0.8):
                self.date_col = True
            else:
                self.date_col = False
        return self.date_col
    
    def get_cardinality(self):
        temp_values = set()
        for cell in self.cells:
            temp_values.add(cell.value)
        return len(temp_values)


class Row(TableEntity):

    def __init__(self, cells):
        super(Row, self).__init__()
        self.cells = cells

    def visualize(self):
        html = "<tr>"
        for cell in self.cells:
            html = html + cell.visualize()
        html = html + "</tr>"
        return html


class Cell(TableEntity):

    def __init__(self, value):
        super(Cell, self).__init__()
        self.value = value
        self.candidates = set()

    def is_NE(self):
        if(self.is_date()):
            return False
        elif(self.is_numeric()):
            return False
        else:
            return True

    def is_numeric(self):
        try:
            float(copy.copy(self.value))
            return True
        except Exception:
            return False

    def is_date(self):
        try:
            date_parser(copy.copy(self.value))
            return True
        except Exception:
            return False

    def visualize(self):
        html_head = "<td title='Actual concept:\n"\
                    +"{}\nPredicted concepts:\n".format(self.true_label)
        html_tail = "'>{}</td>".format(self.value)
        for label in self.predicted_labels:
            html_head = html_head + label[0] + "\n"
        html = html_head + html_tail
        return html


if __name__ == "__main__":
    test_table = Table()
    test_table.parse_csv('sample.csv')
    ne_table = test_table.get_NE_cols()
    for col in ne_table.columns:
        print col.header + ": ",
        print col.get_cardinality()
    ne_table.visualize()