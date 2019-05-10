"""
Routines to export to and import from formatted ASCII files with tab-separated
columns.
Friedrich Schotte, 30 Apr 2008 - 5 Nov 2010
"""

version = "1.5"

from numpy import nan,inf,isnan,isinf

def save(columns,filename,header="",labels=None):
    """Usage: save([x,y],"test.txt",labels="x,y")
    Write lists of numbers as tab-separated ASCII file.
    'columns' must be a list containing lists of numeric values of the same
    length.
    'labels' can be given as comma-spearated string or as list of strings.
    """
    from os.path import exists,dirname
    from os import makedirs,rename,remove
    if not exists(dirname(filename)) and dirname(filename) != "":
        makedirs (dirname(filename))
    
    output = file(filename+".tmp","wb")
    for line in header.split("\n"):
        if line: output.write("# "+line+"\n")
    if labels:
        if isinstance(labels,basestring): labels = labels.split(",")
        output.write("#")
        for col in range(0,len(labels)-1): output.write(str(labels[col])+"\t")
        output.write(str(labels[len(labels)-1])+"\n")
    Ncol = len(columns)
    for row in range(0,len(columns[0])):
        for col in range(0,Ncol):
            val = columns[col][row]
            if isinstance(val,basestring): output.write(val)
            elif isnan(val): output.write("nan")
            elif isinf(val) and val>0: output.write("inf")
            elif isinf(val) and val<0: output.write("-inf")
            else: output.write("%g" % val)
            if col < Ncol-1: output.write("\t")
            else: output.write("\n")
    output.close()
    if exists(filename): remove(filename)
    rename(filename+".tmp",filename)

def read(filename,labels=None,columns=None):
    """Usage:
    x,y = read("test.txt",labels="x,y")
    x,y = read("test.txt",columns=[0,1])
    Reads a tab or space-separated multicolumn ASCII file
    and returns a list of values for each column
    The values are converted to numeric if posiible, otherwise returned as
    strings.
    'labels' can be given as comma-separated string or as list of strings.
    """
    infile = file(filename)
    # First pass: Count number of columns
    Ncol = 0; col_labels = []; last_comment = ""
    line = infile.readline()
    while line != '':
        if line[0:1] == "#": last_comment = line
        else:
            Ncol = max(Ncol,len(line.split()))
            if not col_labels: col_labels = last_comment.strip("# ").split()
        line = infile.readline()
    data = []
    for col in range(0,Ncol): data.append([])

    # Second pass: Read data
    infile.seek(0)
    line = infile.readline()
    while line != '':
        if line[0:1] != "#": # skip comment lines
            fields = line.split()
            for col in range(0,Ncol):
                try: val = fields[col]
                except IndexError: val = ""
                try: val = float(val)
                except ValueError:
                    if val=="NaN" or val=="nan" or val=="-1.#IND": val = nan
                    elif val=="Inf" or val=="inf" or val=="1.#INF": val = inf
                    elif val=="-Inf" or val=="-inf" or val=="-1.#INF": val = -inf
                data[col].append(val)
        line = infile.readline()

    # If column labels are specified, return only those column with matching
    # labels.
    if labels:
        if isinstance(labels,basestring): labels = labels.split(",")
        selected_columns = []; selected_labels = []
        for label in labels:
            if label in col_labels:
                col = col_labels.index(label)
                if col < len(data):
                    selected_columns.append (data[col])
                    selected_labels.append (label)
        data = selected_columns
        col_labels = selected_labels
    # If column numbers are specified, return only those columns.
    if columns:
        selected_columns = []
        for col in columns:
                if col < len(data): selected_columns.append (data[col])
        data = selected_columns

    # Return the columns labels in the parameters "labels"
    if isinstance(labels,list):
        while len(labels) > 0: labels.pop()
        labels += col_labels

    # If only a single column is read, return 1D rather than 2D array.
    if len(data) == 1: return data[0]

    return data

if __name__ == "__main__": # example for testing
    from numpy import array
    from os import remove
    
    x = range(0,6)
    y = [v**2 for v in x]
    x[0] = "0"; y[3] = nan; y[5] = inf
    print "saving",x,y
    save([x,y],"test.txt",header="example",labels="x,y")
    print file("test.txt").read()
    labels=[]
    x,y = array(read("test.txt",labels=labels))
    print "read labels",labels
    print "read data",x,y
    remove("test.txt")
