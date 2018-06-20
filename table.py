from dateutil.parser import parse
import pandas as pd


class TableEntity(object):

    def __init__(self):
        self.labels = []

    def add_label(self, label):
        self.labels.append(label)

    def get_labels(self):
        return self.labels


class Table(TableEntity):

    def __init__(self):
        self.columns = []

    def get_NE_cols(self):
        cols = []
        for column in self.columns:
            if(column.isNE()):
                cols.append(column)
        return cols

    def get_numeric_cols(self):
        cols = []
        for column in self.columns:
            if(column.is_numeric()):
                cols.append(column)
        return cols

    def get_date_cols(self):
        cols = []
        for column in self.columns:
            if(column.is_date()):
                cols.append(column)
        return cols

    def parse_csv(self, file_path):
        temp_df = pd.read_csv(file_path)
        headers = temp_df.dtypes.index
        for header in headers:
            values = temp_df[[header]].values
            cells = []
            for value in values:
                cells.append(Cell(value[0]))
            self.columns.append(Column(header, cells))



class Column(TableEntity):

    def __init__(self, header, cells):
        self.header = header
        self.cells = cells
        self.labels = []
        self.numeric_col = None
        self.date_col = None
        self.NE_col = None

    def is_NE(self):
        if(self.NE_col is None):
            NE_count = 0
            for cell in self.cells:
                if(cell.is_NE()):
                    NE_count += 1
            ne_percentage = float(NE_count)/float(len(self.cells))
            if(ne_percentagec > 0.8):
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
            print numeric_percentage

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


class Cell(TableEntity):

    def __init__(self, value):
        self.value = value

    def is_NE(self):
        if(self.isDate):
            return False
        elif(self, isNumeric):
            return False
        else:
            return True

    def is_numeric(self):
        try:
            float(self.value)
            return True
        except ValueError:
            return False

    def is_date(self):
        try:
            parse(self.value)
            return True
        except ValueError:
            return False


if __name__ == "__main__":
    test_table = Table()
    test_table.parse_csv('sample.csv')