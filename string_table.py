"""
Friedrich Schotte Oct 23, 2014 - Oct 23, 2014
"""
__version__ = "1.0"

class StringTable(object):
    """2D table of strings with labeled columns"""
    filename = ""
    file_timestamp = 0
    filesize = 0
    from collections import OrderedDict
    columns = OrderedDict()
    comment_lines = []
    separator = "\t"

    def __init__(self,filename=None,separator="\t"):
        """"""
        self.separator = separator
        if filename is not None: self.read(filename)

    def set_value(self,column_name,row,value):
        """Set an element
        column_name: string
        row: 0-base integer
        value: string"""
        # Convert value to string if needed.
        value = str(value)
        if not column_name in self.columns: self.columns[column_name] = []
        col = self.columns[column_name]
        if len(col) < row: col += [""]*(row-len(col))
        if row == len(col): col += [value]
        else: col[row] = value

    def set_values(self,column_names,rows,values_list):
        """Modify multiple columns
        column_names: list of strings
        starting_row: 0-base integer        
        values_list: list of lists of strings"""
        for (column_name,values) in zip(column_names,values_list):
            self.set_column_rows(column_name,rows,values)

    def set_column_range(self,column_name,starting_row,values):
        """Modify a column
        columns_name: string
        starting_row: 0-base integer        
        values: list of strings"""
        # Convert values to strings if needed.
        values = [str(value) for value in values]
        if not column_name in self.columns: self.columns[column_name] = []
        col = self.columns[column_name]
        if len(col) < starting_row+1: col += [""]*(starting_row+1-len(col))
        col = col[0:starting_row]+values+col[starting_row+len(values):]
        self.columns[column_name] = col

    def set_column_rows(self,column_name,rows,values):
        """Modify a column
        columns_name: string
        rows: 0-base integer        
        values: list of strings"""
        for (row,value) in zip(rows,values): self.set_value(column_name,row,value)

    def __len__(self):
        """Number of rows"""
        if len(self.columns) == 0: return 0
        return max([len(col) for col in columns])

    @property
    def column_names(self):
        """labels of columns. List of strings"""
        return self.columns.keys()

    def read(self,filename=None):
        """Load from mutli-column text file with column name header"""
        from os.path import getmtime
        if filename is None: filename = self.filename
        text = file(filename,"rb").read()
        self.set_text(text)
        self.filename = filename
        self.file_timestamp = getmtime(filename)
        self.filesize = len(text)

    def save(self,filename=None):
        """Generate mutli-column formatted text file with column
        name header"""
        from os.path import exists,getmtime,dirname
        from os import makedirs
        if filename is None: filename = self.filename
        directory = dirname(filename)
        if directory != "" and not exists(directory): makedirs(directory)
        text = str(self)
        file(filename,"wb").write(text)
        self.filename = filename
        self.file_timestamp = getmtime(filename)
        self.filesize = len(text)

    def reread(self,filename=None):
        """Reload the table if the file contents has changed since it was read
        the first time."""
        from os.path import exists,getmtime,getsize
        if filename is None: filename = self.filename
        if exists(filename):
            if filename != self.filename or \
               getmtime(filename) != self.file_timestamp or \
               getsize(filename) != self.filesize:
                  ##print("re-reading %r" % filename)
                  self.read(filename)
        else:
            self.filename = filename    
            self.file_timestamp = 0.0   
            self.filesize = 0    

    def clear(self):
        """Reset to empty table"""
        self.comments = []
        from collections import OrderedDict
        self.columns = OrderedDict()
        self.filename = ""
        self.file_timestamp = 0.0
        self.separator = "\t"

    def __str__(self):
        """Table as formmatted text"""
        text = ""
        for line in self.comment_lines: text += "# "+line+"\n" 
        if len(self.columns) > 0:
            text += "#"+self.separator.join(self.columns.keys())+"\n"
            columns = self.columns.values()
            N = max([len(col) for col in columns])
            for i in range(0,N): text += \
                self.separator.join(
                    [col[i] if i<len(col) else "" for col in columns])+"\n"
        return text

    def set_text(self,text):
        """Populate the table from formatted text"""
        self.comment_lines = []
        from collections import OrderedDict
        self.columns = OrderedDict()

        text = UNIX_text(text)
        lines = text.strip("\n").split("\n")
        Nlines = len(lines)
        column_names = []
        row = 0
        for i in range(0,Nlines):
            if lines[i].startswith("#"):
                if i+1 < Nlines and not lines[i+1].startswith("#"):
                    column_names = lines[i][1:].split(self.separator)
                else:
                    comment = lines[i][1:]
                    if comment.startswith(" "): comment = comment[1:]
                    self.comment_lines += [comment]
            else:
                values = lines[i].split(self.separator)
                for i in range(0,min(len(values),len(column_names))):
                    self.set_value(column_names[i],row,values[i])
                row += 1

    def add_comment(self,comment):
        """Add a comment to be save in the header of the file."""
        self.comment_lines += [comment]

    def get_comments(self):
        """Comments to be save in the header of the file.
        multiline string"""
        return "\n".join(self.comment_lines)
    def set_comments(self,value):
        # Is value a multiline string?
        if "\n" in value: value = value.strip("\n").split("\n")
        # Is value a string?
        if isinstance(value,basestring): value = [value]
        self.comment_lines = value
    comments = property(get_comments,set_comments)
                
    def __repr__(self):
        return "StringTable(%r)" % self.filename

string_table = StringTable

def UNIX_text(text):
    """Convert line breaks from DOS/Windows or Macintosh to UNIX convention.
    DOS/Windows: '\n\r', Macinosh: '\r':, UNIX: '\n'"""
    if not "\r" in text: return text # already in UNIX format
    text = text.replace("\n\r","\n") # was DOS to UNIX
    text = text.replace("\r\n","\n") # was ? to UNIX
    text = text.replace("\r","\n") #  MAC to UNIX
    return text


if __name__ == "__main__": # for testing
    from pdb import pm
    t = string_table()
    self = t # for debugging
    t.comments = "This is a test."
    t.set_values(["A","B"],range(0,4),[range(1,4),range(11,14)])
    print(t)
    t.save("test/test.txt")
    t.read("test/test.txt")
    t.reread()
    print(t)
