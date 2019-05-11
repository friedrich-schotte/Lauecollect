"""The 'table' class is to work with multi-column formatted ASCII files.
It provides a record array interface.
Friedrich Schotte, 22 Aug 2009 - 3 Aug 2017
"""
from __future__ import division # int/int = float
from numpy import recarray
from logging import debug
try: from status import status
except ImportError:
    def status(*args): pass
try: from collections import OrderedDict
except ImportError: OrderedDict = dict

__version__ = "6.9.9" # dtype: numpy.dtype, recarray.__getattribute__

# Data members of 'table' in addition to recarray.
attributes = ["filename","separator","format","unitcell","info",
              "file_timestamp","filesize","default_dtype"]

class table(recarray):
    """Extension of record array with easier to use API."""

    # "table" is a subclass of "recarray".  
    # Because "recarray" uses a __new__ rather than an __init__ constructor,
    # __new__ rather than __init__ needs to be overridden.
    def __new__(subclass,*args,**keyword_arguments):
        # Called by Python when creating a new object of type 'table'
        # The remaining arguments after 'subclass' are used only by '__init__'.
        ##debug("table.__new__(subclass=%r,%r" % (subclass,keyword_arguments))
        self = recarray(0,dtype=[("__dummy__",float)]) ##recarray?
        # To get an ndarray subclass that owns its own data, copy() must be
        # called. Otherwise, "resize" will fail. ("cannot resize this array:
        # it does not own its data")
        return self.view(subclass).copy()

    def __init__(self,filename=None,rows=0,columns=None,dtype=None,
        format="",separator=None,data=None,shape=None,text=None):
        """filename: from which file to load data from.
        If 'format' is not specified the file's extension determines the
        format.
        Extension .mtz: CCP4 X-ray reflection data format
        Extension .hdf5: Hierarchical Data Format version 5
        Extension .nc: NetCDF (Network Common Data Form, version 2)
        Extension .mat: MATLAB version 5
        Extension .pkl: Python's Pickle format (Needs to have been generated
        by the 'save' method.)
        A filename with any other extension is treated as a formatted ASCII
        text file, with multiple columns, separated by tab or space.
        (Can be overridden by the 'separator' option.)
        dtype: list of tuples e.g. [("H",int),("K",int),("L",int)]
        rows: size of record array
        columns: list of strings, e.g. ["H","K","L"]
        (Only one of either 'columns' or 'dtype' must be specified.)
        separator: (if 'filename' is given) column separator for text
        file, e.g. " " for space or "\t" for tab.
        Default: None = Any whitespace string is a separator.
        format: 'text','MTZ','HDF5','NetCDF',''MATLAB', or 'pickle'.
        Overrides file format based on file extension.
        data: list of arrays to initialize the table.
        shape: tuple, to create a multi-dimensional record array
        text: formatted ASCII text, tab or space separated columns, with
        column label header line.
        """
        # 'shape' is an alias for rows.
        if shape is not None: rows = shape
        self.format = format
        self.separator = separator
        if filename is not None:
            self.read(filename,format=format,separator=separator); return

        if text is not None: self.fromtext(text,separator=separator); return
            
        if data is not None:
            from numpy import asanyarray,array,max
            data = [asanyarray(d) for d in data]
            if rows == 0: rows = max([array(d.shape) for d in data],axis=0)
            if dtype is not None:
                dtypes = [(col,dtype) for col in columns]
                data = [d.astype(dtype) for d in data]
            else:
                dtypes = [(col,array_dtype(d)) for col,d in zip(columns,data)]
            ##debug("table.__init__: dtypes: %r" % dtypes)
            self.reset(rows=rows,dtype=dtypes)
            ##debug("table.__init__: columns: %r" % (self.columns))
            for i in range(0,len(self.columns)): self[self.columns[i]] = data[i]
            return
            
        self.reset(rows=rows,columns=columns,dtype=dtype)            

    def __array_finalize__(self,table):
        """Called after a 'table' object has been copied.
        Passes non-array attributes from the original to the new Map object."""
        ##debug("__array_finalize__")
        self.filename = getattr(table,"filename","")
        self.separator = getattr(table,"separator",None)
        self.format = getattr(table,"format","")
        if hasattr(table,"unitcell"): self.unitcell = table.unitcell
        self.info = getattr(table,"info",OrderedDict())
        self.file_timestamp = getattr(table,"file_timestamp",0.0)
        self.filesize = getattr(table,"filesize",0)
        self.default_dtype = getattr(table,"default_dtype","f4")

    def __str__(self): return self.astext

    def reset(self,rows=0,columns=None,dtype=None):
        """Change the size and the data format,
        without preserving the contents.
        rows: new size, may be a tuple to make the table multidimensional
        columns: list of strings, e.g. ["H","K","L"]
        dtype: list of tuples e.g. [("H",int),("K",int),("L",int)]
        (Only one of either 'columns' or 'dtype' must be specified.)
        Floating point valued columns are initialized to with NaNs,
        integer valued columns with zeros."""
        ##debug("reset(self,rows=%r,columns=%r,dtype=%r)" % (rows,columns,dtype))
        from numpy import array,product,nan,int8
        import numpy # for numpy.dtype

        if columns is not None and dtype is not None:
            dtype = zip(columns,[dtype]*len(columns))
        if columns is not None and dtype is None:
            dtype = zip(columns,[float]*len(columns))
        if dtype is None or dtype == []: dtype = [("__dummy__",float)]
        ##debug("reset: rows=%r, dtype=%r" % (rows,dtype))
        # The data type can only be changed safely when the size is zero.
        recarray.resize(self,0,refcheck=False)
        # The statement "self.dtype = int8" is needed, otherwise an exception
        # occurs: "ValueError: new type not compatible with array"
        self.dtype = numpy.dtype(int8)
        self.dtype = numpy.dtype(dtype)

        shape = rows
        size = product(shape)
        recarray.resize(self,size,refcheck=False)
        self.shape = shape
        self.erase()

    def erase(self):
        """Fill the table with a default value for each columns' data type.
        (0 for int, nan for float, empty string for string)"""
        for col in self.columns: erase(self[col])

    def resize(self,shape):
        """Change the size, preserving the content.
        shape: new size, may be a tuple in case the table is multidimensional
        If table is 1-dim. shape is the numnr of rows.
        If the new size is larger than the current, missing values are filled
        with NaNs, in the case of floating point values, or zeros in the
        case of integer values"""
        from numpy import atleast_1d,all,minimum,maximum,indices
        shape = tuple(atleast_1d(shape))
        if all(self.shape == shape): return
        ##debug("resize: resizing from %r to %r" % (self.shape,shape))
        content = self.copy()
        self.reset(rows=shape,dtype=self.dtype)
        # Copy the old content to the resized space.
        overlap = minimum(content.shape,self.shape)
        self[tuple(indices(overlap))] = content[tuple(indices(overlap))]

    def set_dtype(self,dtype):
        """Add or remove columns or change the data type of existing
        columns, preserving the content.
        tables_in: list of tables
        Return value: list of tables"""
        if self.dtype == dtype: return
        content = self.copy()
        self.reset(rows=self.shape,dtype=dtype)
        for column in content.columns:
            if self.has_column(column): self[column] = content[column]

    def read(self,filename=None,format="",separator=None):
        """filename: pathname of the input file
        If 'format' is not specified the file's extension determines the
        format.
        Extension .mtz: CCP4 X-ray reflection data format
        Extension .hdf5: Hierarchical Data Format version 5
        Extension .nc: NetCDF (Network Common Data Form, version 2)
        Extension .mat: MATLAB version 5
        Extension .pkl: Python's Pickle format (Needs to have been generated
        by the 'save' method.)
        A filename with any other extension is treated as a formatted ASCII
        text file, with multiple columns, separated by tab or space.
        (Can be overridden by the 'separator' option.)
        separator: column separator for text
        file, e.g. " " for space or "\t" for tab.
        Default: None = Any whitespace string is a separator.
        format: 'text','MTZ','HDF5','MATLAB','pickle'.
        Overrides file format based on file extension.
        """
        if filename is None: filename = self.filename
        # Multiple filenames generate a 2D table.
        if isarray(filename):
            self.read_multifile(filename,format,separator)
            return
        if not format: format = self.guess_format(filename)
        if not format: format == self.format
        if not format: format = "text"
        format = format.upper()
         
        if format in ["MTZ"]: from MTZ import mtzread; mtzread(self,filename)
        elif format in ["CIF","MMCIF"]:
            from CIF import read_CIF; read_CIF(self,filename)
        elif format in ["HDF5","HD5","H5"]: self.read_HDF5(filename)
        elif format in ["NETCDF","NC"]: self.read_NetCDF(filename)
        elif format in ["MATLAB","MAT"]: self.read_MATLAB(filename)
        elif format in ["PICKLE","PKL"]: self.read_pickle(filename)
        elif format in ["TEXT","TXT"]: self.read_text(filename,separator)
        else:
            print "%s: Unknown format %r. Assuming text" % (filename,format)
            self.read_text(filename,separator)

    def read_multifile(self,filenames,format="",separator=None):
        """Read several file to produce a 2D table"""
        from numpy import row_stack
        data = [table(f,format=format,separator=separator) for f in filenames]
        data = row_stack(tables_with_same_columns(data)).view(table)
        self.assign(data)
        self.filename = filenames
        self.format = format
        self.file_timestamp = file_timestamp(self.filename)
        self.filesize = filesize(self.filename)
        
    def assign(self,data):
        """Make the current table a copy of the table 'data'"""
        self.reset(rows=data.rows,dtype=data.dtype)
        self[:] = data[:]

    @staticmethod
    def guess_format(filename):
        "Try to guess the map file format based in extension of the file name"
        from os.path import basename,splitext
        name = basename(filename)
        ext = splitext(filename)[1].lower()
        if ext in [".mtz"]: return "MTZ"
        if ext in [".cif","mmcif"]: return "CIF"
        elif ext in [".pkl",".pickle"]: return "pickle"
        elif ext in [".hdf5",".hd5",".h5"]: return "HDF5"
        elif ext in [".nc",".netcdf"]: return "NetCDF"
        elif ext in [".mat",".matlab"]: return "MATLAB"
        elif ext in [".txt",".tsv",".hkl",".log"]: return "text"
        else: return ""

    def read_HDF5(self,filename):
        """Read a file in HDF5 format."""
        import tables
        h5file = tables.openFile(filename)
        columns = h5file.root._v_children.keys()
        data = {}
        for column in columns: data[column] = h5file.getNode("/"+column)
        dtype = [(column,data[column].dtype) for column in columns]
        first_column = getattr(h5file.root,columns[0])
        rows = first_column.shape
        self.reset(dtype=dtype,rows=rows)
        for column in columns: self[column] = data[column]
        self.filename = filename
        self.format = "HDF5"
        self.file_timestamp = file_timestamp(self.filename)
        self.filesize = filesize(self.filename)

    def read_NetCDF(self,filename):
        """Read a file in NetCDF (Network Common Data Form) format.
        vesion 1 or 2, version 4.0 not supported"""
        from scipy.io import netcdf_file
        f = netcdf_file(filename)
        # "columns" is not a standard feature of 'netcdf_file', but used
        # by "write_NetCDF" to preserve the order of the columns,
        # which is not preserved in 'f.variables.keys()'
        if hasattr(f,"columns"): columns = f.columns.split(",")
        else: columns = f.variables.keys()
        data = {}
        for column in columns: data[column] = f.variables[column].data
        shape = data[columns[0]].shape
        types = [data[column].dtype for column in columns]
        # Ignore byte order ("<" = little endian, ">" = big endian) in data type
        types = [type.descr[0][1].strip("><") for type in types]
        dtype = zip(columns,types)
        self.reset(dtype=dtype,rows=shape)
        for column in columns: self[column] = data[column]
        self.filename = filename
        self.format = "NetCDF"
        self.file_timestamp = file_timestamp(self.filename)
        self.filesize = filesize(self.filename)

    def read_MATLAB(self,filename):
        """Read a file in MATLAB (version 5) format."""
        from scipy.io import loadmat
        mdict = loadmat(filename)
        columns = [str(column).strip() for column in mdict["columns"]]
        rows = mdict[columns[0]].shape
        types = [mdict[column].dtype for column in columns]
        self.reset(rows=rows,dtype=zip(columns,types))
        for column in columns: self[column] = mdict[column]
        self.filename = filename
        self.format = "MATLAB"
        self.file_timestamp = file_timestamp(self.filename)
        self.filesize = filesize(self.filename)

    def read_pickle(self,filename):
        """Read a file in Python's pickle format.
        Only works if file has been generate with the 'save_pickle'
        method."""
        from numpy import load
        table = load(filename)
        self.reset(dtype=table.dtype,rows=table.rows)
        self[:] = table[:]
        self.filename = filename
        self.format = "pickle"
        self.file_timestamp = file_timestamp(self.filename)
        self.filesize = filesize(self.filename)

    def read_text(self,filename,separator=None):
        """Read a tab or space-separated multicolumn ASCII file
        and returns a numpy array of for each column, as dictonary, indexed
        by the column label.
        The values are converted to numeric if possible, otherwise returned as
        strings."""
        ##debug("Reading file")
        import codecs
        text = codecs.open(filename,encoding="utf-8",mode="rb").read()
        self.fromtext(text,separator=separator)
        self.filename = filename
        self.format = "text"
        self.file_timestamp = file_timestamp(self.filename)
        self.filesize = filesize(self.filename)

    def reread(self,filename=None,separator=None):
        """Reload the table if the file contents has changed since it was read
        the first time."""
        from os.path import exists
        if filename is None: filename = self.filename
        if self.filename != filename:
            self.reset(0)
            self.file_timestamp = 0
            self.filesize = 0
        if exists(filename):
            if filename != self.filename or \
               file_timestamp(filename) != self.file_timestamp or \
               filesize(filename) != self.filesize:
                self.read(filename,separator=separator)
        else: self.filename = filename

    def reread_needed(self,filename=None):
        """Reload the table if the file contents has changed since it was read
        the first time?"""
        from os.path import exists
        if filename is None: filename = self.filename
        if self.filename != filename: return True
        if exists(filename):
            if filename != self.filename or \
               file_timestamp(filename) != self.file_timestamp or \
               filesize(filename) != self.filesize:
                return True
        return False

    def save(self,filename=None,format=""):
        """Writes contents to a file.
        filename:
        If 'format' is not specified the file's extension determines the
        format.
        Extension .mtz: CCP4 X-ray reflection data format
        Extension .hdf5: Hierarchical Data Format version 5
        Extension .nc: NetCDF (Network Common Data Form)
        Extension .mat: MATLAB version 5
        Extension .pkl: Python's Pickle format (Needs to have been generated
        by the 'save' method.)
        If the filename has any other extension, a formatted ASCII
        text file with multiple columns, separated by tabs, is generated.
        format: 'text','MTZ','HDF5','MATLAB','pickle'.
        Overrides file format based on file extension.
        """
        ##debug("save(filename=%r,format=%r)" % (repr(filename),repr(format)))
        if filename is None: filename = self.filename

        # A 2D array may be saved to multiple files.
        if isarray(filename): self.save_multifile(filename,format); return

        if not format: format = self.guess_format(filename)
        if not format: format == self.format
        if not format: format = "text"
        format = format.upper()

        if format in ["MTZ"]: from MTZ import mtzsave; mtzsave(self,filename)
        elif format in ["HDF5","H5"]: self.save_HDF5(filename)
        elif format in ["MATLAB","MAT"]: self.save_MATLAB(filename)
        elif format in ["PICKLE","PKL"]: self.save_pickle(filename)
        elif format in ["TEXT","TXT"]: self.save_text(filename)
        elif format in ["NETCDF","NC"]: self.save_NetCDF(filename)
        else:
            print "%s: Unknown format %r. Generating text file" % (filename,format)
            self.save_text(filename)
            
    write = save # Make "write" an alias for "save".
        
    def save_multifile(self,filenames,format):
        """A 2D array may be written to multiple files."""
        ##debug("save_multifile(filenames=%r,format=%r)" % (repr(filenames),repr(format)))
        for i in range(0,min(len(self),len(filenames))):
            status("Saving",i/len(filenames))
            self[i].save(filenames[i],format)
        status("Saving",1)
        self.filename = filenames

    def save_HDF5(self,filename):
        """Write a table object to a file in HDF5 format."""
        if filename == "": return
        self.makedir(filename)
        import tables
        h5file = tables.openFile(filename,mode='w')
        for column in self.columns:
            h5file.createArray(h5file.root,column,self[column])
        h5file.close()
        self.filename = filename
        self.format = "HDF5"
        self.file_timestamp = file_timestamp(self.filename)
        self.filesize = filesize(self.filename)

    def save_NetCDF(self,filename):
        """Write a table object to file in NetCDF (Network Common Data Form)."""
        if filename == "": return
        self.makedir(filename)
        from scipy.io import netcdf_file
        f = netcdf_file(filename,mode="w",version=2)
        f.history = "Created by table.py "+__version__
        # Save information about the order of the columns.
        columns = ""
        for column in self.columns: columns += column+","
        columns = columns.rstrip(",")
        f.columns = columns
        # NetCDF fomrmat requires labels for dimensions.
        dim_labels = ["x","y","z"][0:self.ndim]
        for i in range(0,self.ndim):
            f.createDimension(dim_labels[i],self.shape[i])
        for column in self.columns:
            v = f.createVariable(column,self[column].dtype.char,dim_labels)
            v[:] = self[column]
        f.close()
        self.filename = filename
        self.format = "NetCDF"
        self.file_timestamp = file_timestamp(self.filename)
        self.filesize = filesize(self.filename)

    def save_MATLAB(self,filename):
        """Write a table object to file in MATLAB data format (version 5)."""
        if filename == "": return
        self.makedir(filename)
        from scipy.io import savemat
        mdict = {"columns": self.columns}
        for column in self.columns: mdict[column] = self[column]
        savemat(filename,mdict,oned_as='row')
        self.filename = filename
        self.format = "MATLAB"
        self.file_timestamp = file_timestamp(self.filename)
        self.filesize = filesize(self.filename)

    def save_pickle(self,filename):
        """Write a table object to file in HDF5 format."""
        from os import rename,remove; from os.path import exists
        if filename == "": return
        self.makedir(filename)
        self.dump(filename+".tmp")
        if exists(filename): remove(filename)
        rename(filename+".tmp",filename)
        self.filename = filename
        self.format = "pickle"
        self.file_timestamp = file_timestamp(self.filename)
        self.filesize = filesize(self.filename)

    def save_text(self,filename):
        """Writes each column as tab-separated ASCII file."""
        if filename == "": return
        text = self.astext
        # Update the file only if needed. This way, the file_timestamp does not change
        # when the contents of the file remains unchanged.
        try: file_content = file(filename).read()
        except IOError: file_content = None
        if text != file_content:
            # Write formatted text to file.
            # Make sure not to leave the file in an "unfinished" state at
            # any time.
            self.makedir(filename)
            file(filename+".tmp","wb").write(text)
            from os import rename,remove; from os.path import exists
            if exists(filename): remove(filename)
            rename(filename+".tmp",filename)
        self.filename = filename
        self.format = "text"
        self.file_timestamp = file_timestamp(self.filename)
        self.filesize = filesize(self.filename)

    @staticmethod
    def makedir(filename):
        """Make sure that the directory of the given filename exists."""
        from os.path import exists,dirname
        from os import makedirs
        directory = dirname(filename)
        if directory != "" and not exists(directory): makedirs(directory)

    def fromtext(self,text,separator=None):
        """Convert a tab or space-separated multicolumn formatted test
        to a 'table' object, replacing the current contents of the table.
        """
        from numpy import nan,inf,isnan,isinf,array,float32,float64,int32,int16,int8

        ##debug("Splitting into lines")
        lines = UNIX_text(text).split("\n")
        ##debug("Text to binary: pass 1")
        # First pass: Count number of columns
        Ncol = 0; Nrow = 0; header_line = ""
        for line in lines:
            if line.startswith("#"): header_line = line
            elif line == "": pass # skip empty lines
            else:
                Ncol = max(Ncol,len(split(line,separator)))
                Nrow += 1

        if header_line == "" and len(lines)>0: header_line = lines[0]
        labels = split(header_line.strip("# "),separator)
        for col in range(len(labels),Ncol): labels.append("%d"%col)

        data = []
        for col in range(0,Ncol): data.append([])

        # Second pass: Read data
        ##debug("Text to binary: pass 2")
        info = OrderedDict()
        for line in lines:
            if line == header_line:
                pass # skip header line
            elif line.startswith("#"):
                # Interpret comment lines as key/value pairs to be put into
                # the table's info dictionary.
                # '# input_dir: "//Femto/C/Data/2010.02"'
                # -> info["input_dir"] = "//Femto/C/Data/2010.02"
                comment = line[1:].strip()
                if ":" in comment: n = comment.find(":")
                elif "=" in comment: n = comment.find("")
                else: n = len(comment)
                keyword,value = comment[0:n].strip(),comment[n+1:].strip()
                try: value = eval(value)
                except: pass
                if keyword: info[keyword] = value
            elif line == "": pass # skip empty lines
            else:
                fields = split(line,separator)
                for col in range(0,Ncol):
                    try: val = fields[col]
                    except IndexError: val = ""
                    if isinstance(val,unicode):
                        try: val = str(val)
                        except UnicodeEncodeError: pass
                    if isinstance(val,basestring):
                        try: val = int(val)
                        except ValueError: pass
                    if isinstance(val,basestring):
                        try: val = float(val)
                        except ValueError: pass
                    if isinstance(val,basestring):
                        if val in ("NaN","nan","-1.#IND","N.A."): val = nan
                        elif val in ("Inf","inf","1.#INF"): val = inf
                        elif val in ("-Inf","-inf","-1.#INF"): val = -inf
                    data[col].append(val)

        # Convert columns to numpy array.
        ##debug("Converting to numpy array")
        for col in range(0,Ncol): data[col] = array(data[col])

        # Reduce the memory footprint of the arrays as much as possible.
        ##debug("Optimizing data types")
        for col in range(0,Ncol): 
            ##if data[col].dtype == float64:
            ##    data[col] = array(data[col],float32)
            try:
                for dtype in int16,int8,bool:
                    if all(data[col] == array(data[col],dtype)):
                        data[col] = array(data[col],dtype)
            except ValueError: pass

        # Convert columns to record array.
        ##debug("Converting  to record array")
        types = [data[col].dtype for col in range(0,Ncol)]
        
        # I a numpy array,field name may not be a unicode string, but it may be
        # a 2-tuple (title,name), where title may be unicode string.
        for i in range(0,len(labels)):
            if asstr(labels[i]) != labels[i]:
                labels[i] = (labels[i],asstr(labels[i]))
            else: labels[i] = asstr(labels[i])
        
        self.reset(rows=Nrow,dtype=zip(labels,types))
        self.info = info
        for col in range(0,Ncol): self[labels[col]] = data[col]

        self.to2D()

    def to2D(self):
        """Convert table to 2D table"""
        # If the table was loaded from a text file and the column conform to
        # to convention "col[1]","col[2]",..., the text file was saved from
        # a 2D table.
        from numpy import array,where
        if not any(["[" in col for col in self.columns]): return
        columns = array([col.split("[")[0] for col in self.columns])
        indices = [col.split("[")[1].replace("]","") if "[" in col else ""
                   for col in self.columns]
        def toint(x):
            try: return int(x)
            except: return 0
        indices = array([toint(i) for i in indices])
        if all(indices == 0): return
        # If the smallest index is 1, assume the indices are counted starting with 1.
        if min(indices) == 1: indices -= 1
        ##debug("to2D: indices = %r" % indices)
        shape = max(indices)+1,self.rows
        indices0 = [where(columns == col)[0][0] for col in unique(columns)]
        dtypes = [self[columns[i]].dtype for i in indices0]
        dtype = zip(unique(columns),dtypes)
        data = table(dtype=dtype,shape=shape)
        for i in range(0,len(self.columns)):
            if indices[i] >= 0:
                data[columns[i]][indices[i]] = self[self.columns[i]]
            else: data[columns[i]] = self[columns[i]]
        self.assign(data)

    def totext(self):
        """Convert to formatted text, as tab-separated columns"""
        if self.ndim > 1: return self.to_text_2D()
        if len(self.columns) == 0: return ""
        
        from numpy import isnan,isinf
        text = ""
        # Generate info header
        for keyword in self.info:
            value = self.info[keyword]
            if not isinstance(value,basestring): value = repr(value)
            if value != "": text += "# %s: %s\n" % (keyword,value)
            else: text += "# %s\n" % keyword
        # Generate column header line.
        line = "#"
        for column in self.columns: line += column+"\t"
        text += line.rstrip("\t")+"\n"
        # Format table data.
        for row in range(0,len(self)):
            line = ""
            values = self[row]
            for i in range(0,len(values)):
                line += tostr(values[i])
                line += "\t" if i < len(values)-1 else "\n"
            text += line
        return text
    astext = property(totext)
        
    def to_text_2D(self):
        """Convert to formatted text, as tab-separated columns"""
        from numpy import isnan,isinf
        text = ""
        # Generate info header
        for keyword in self.info:
            text += "# %s = %r\n" % (keyword,self.info[keyword])
        # Generate multiple columns for a column only if those columns are
        # actually different.
        expand = [not samerow(self[col]) for col in self.columns]
        # Write column header line.
        M,N = self.shape
        Ncol = len(self.columns)
        line = "#"
        for icol in range(0,Ncol):
            if expand[icol]:
                for i in range(0,M): line += "%s[%d]\t" % (self.columns[icol],i+1)
            else: line += self.columns[icol] + "\t"
        text += line.rstrip("\t")+"\n"
        # Write column data.
        for row in range(0,N):
            line = ""
            row_data = self[:,row]
            for icol in range(0,Ncol):
                if expand[icol]:
                    for i in range(0,M):
                        line += tostr(row_data[i][icol])
                        line += "\t"
                else:
                    line += tostr(row_data[0][icol])
                    line += "\t"                    
            text += line.strip("\t")+"\n"
        return text

    def add_column(self,name,value=None,dtype=None):
        self.add_columns([name],values=[value],dtypes=[dtype])

    def add_columns(self,names,values=None,dtypes=None):
        """Append a new column to the table."""
        from numpy import asarray,array,copy,nan,issubdtype
        import numpy
        from collections import OrderedDict

        names = asarray(names)

        if values is None: values = [None]*len(names)
        if dtypes is None: dtypes = [None]*len(names)

        for i in range(0,len(names)):
            if dtypes[i] is None: 
                if values[i] is not None: dtypes[i] = array(values[i]).dtype
                else: dtypes[i] = self.column_dtype(names[i])

        new_dtype = OrderedDict(self.dtype.descr)
        for (name,dtype) in zip(names,dtypes):
            if name in new_dtype:
                new_dtype[name] = common_dtype(new_dtype[name],dtype)
            else: new_dtype[name] = dtype       
        
        if len(new_dtype) > 1: # Remove dummy column if present.
            if "__dummy__" in new_dtype: del new_dtype["__dummy__"]

        new_dtype = numpy.dtype(zip(new_dtype.keys(),new_dtype.values()))

        if new_dtype != self.dtype: 
            # Save content, change size, restore content.
            content = self.copy()        
            self.reset(rows=self.rows,dtype=new_dtype)
            for column in content.columns: self[column] = content[column]
        
        # Initialize the new columns.
        for (name,value) in zip(names,values):
            if value is not None: self[name] = value

    def column_dtype(self,name):
        """Data type of a column"""
        if not self.has_column(name): return self.default_dtype
        return self[name].dtype

    def rename_column(self,old_name,new_name):
        """Change the name of a column label"""
        dtype = self.dtype.descr
        for i in range(0,len(dtype)):
            (name,type) = dtype[i]
            if name == old_name: dtype[i] = (new_name,type)
        self.dtype = dtype

    def delete_column(self,name):
        """Remove a column.
        name: label of columns to be removed"""
        self.delete_columns([name])

    def delete_columns(self,names):
        """Remove a mutiple columns.
        names: list of labels of columns to be removed"""
        columns = list(self.columns)
        dtype = self.dtype.descr
        for name in names:
            name = self.matching_column(name)
            if name == "": continue
            if not name in columns: continue
            i = columns.index(name)
            columns.pop(i)
            dtype.pop(i)
        if columns == list(self.columns): return
        # Save content, change size, restore content.
        content = self.copy()        
        self.reset(rows=self.rows,dtype=dtype)
        for column in columns: self[column] = content[column]

    def get_columns(self):
        """list of column labels as numpy array"""
        from numpy import array,chararray
        columns = [d[0] for d in self.dtype.descr]
        # Field names may be (title,name) 2-tuples. In this case the title counts.
        columns = [d[0] if type(d)==tuple else d for d in columns]
        columns = [d for d in columns if d != '__dummy__']
        if len(columns) > 0: columns = array(columns)
        else: columns = array([],dtype=str)
        columns = columns.view(chararray)
        return columns
    def set_columns(self,new_labels):
        from numpy import array
        labels = list(array(self.dtype.descr)[:,0])
        dtypes = array(self.dtype.descr)[:,1]
        n = min(len(labels),len(new_labels))
        labels[0:n] = new_labels[0:n]
        self.dtype = zip(labels,dtypes)
    columns = property(get_columns,set_columns)

    def has_column(self,name):
        """Does table have a field labeled 'name'?
        name: string, not case sensitive"""
        for column_name in self.columns:
            if matches(name,column_name): return True
        return False

    def matching_column(self,name):
        """Convert an approximate column label into an exact label.
        E.g. 'sample_temp' -> 'Sample-Temp[C]'
        name: string, not case sensitive
        Return value: string; empty string if not match was found"""
        columns_names = self.columns
        if name in columns_names: return name
        for column_name in columns_names:
            if matches(name,column_name): return column_name
        return ""

    def get_rows(self):
        """number of rows, if one dimensional;
        shape, if muti-dimensional"""
        if self.ndim == 1: return self.size
        else: return self.shape
    def set_rows(self,rows): self.resize(rows=rows)
    rows = property(get_rows,set_rows)

    def toarray(self):
        """Convert from record array to normal array.
        The columns become an extra dimension.
        Return value: array of size Ncols x Nrows.
        If the column data type is mixed, e.g.'int' and 'float'
        the data type becomes 'float' for all columns.
        If it is 'float' and string, then it comes string."""
        from numpy import array
        return array([self[column] for column in self.columns])
    asarray = property(toarray)
        
    def to_hklset(self):
        """Return 'table' object, with columns H, K, L, plus the
        columns of the 'Hklset' object.
        Indices H,K,L with all columns NaN in the input are omitted in
        the table."""
        from hklset import Hklset
        return Hklset(table=self)
    as_hklset = property(to_hklset)

    def assign_column(self,name,value):
        """name: column label"""
        ##debug("assign_column(%r,%r)" % (name,value))
        self.add_column(name,dtype=array_dtype(value))
        from numpy import atleast_1d,asanyarray
        value = atleast_1d(value)
        table_shape,value_shape = common_shape(self.shape,value.shape)
        value = resize_array(value,value_shape)
        self.resize(table_shape)
        recarray.__setitem__(self,name,value)

    def assign_columns(self,columns,value):
        """Change multiple columns at once
        columns: list of strings"""
        if type(value) == table:
            # Handle case: data["H","K","L"] = data["H","K","L"]
            for i in range(0,len(columns)):
                self[columns[i]] = value[value.columns[i]]
        else:
            # Handle case:  data["H","K","L"] = zeros(3,Ncol)
            for i in range(0,len(columns)): self[columns[i]] = value[i]
        # TO DO: handle value of type record array.

    def make_dtype_compatible(self,value):
        """Make sure that table has at least all the columns 'value' has"""
        if not istable(value): return
        if self.dtype == value.dtype: return
        dtype = common_dtypes([self,value])
        self.set_dtype(dtype)    
        
    def subtable(self,columns):
        """A table consisting of a subset of columns of this table.
        columns: list of strings
        Return value: table object"""
        return table(columns=columns,data=[self[col] for col in columns])
        
    def formula(self,formula):
        """Calculate a combination of columns according to a formula
        Formula: e.g. '1+R' if the table has a column name 'R'"""
        for column in self.columns: locals()[column] = self[column]
        return eval(formula)

    def __setitem__(self,item,value):
        """Called when 'table[item] = value' is used.
        Extends the functionality of recarray, allowing adding new columns."""
        ##debug("table.__setitem__(%r)" % item)
        if isstring(item): self.assign_column(item,value); return
        if is_string_array(item): self.assign_columns(item,value); return
        self.make_dtype_compatible(value)
        value = make_dtype_compatible(value,self)
        try: recarray.__setitem__(self,item,value); return
        except IndexError,exception: extype = IndexError # data[["H","K","L"]]
        except ValueError,exception: extype = ValueError # data["H","K","L"]
        ##debug("recarray.__setitem__: %s: %s" % (extype,exception))
        # Handle cases 'data[["H","K","L"]] = ...' and 'data["H","K","L"] = ...'
        raise extype,exception

    def __getitem__(self,item):
        """Called when 'table[item]' is used.
        Extends the functionality of recarray, allowing adding new columns."""
        ##debug("table.__getitem__(%r)" % item)
        # Problem: the built-in support for data[["L","H","K"]] may return the
        # a record array with the columns in a different order than specified,
        # e.g. "H","K","L".
        if is_string_array(item): return self.subtable(item)
        try: return adjust_type(recarray.__getitem__(self,item))
        except ValueError,exception: pass
        if isstring(item):
            # Allow data["phi"] for data["phi[deg]"].
            for column_name in self.columns:
                if matches(item,column_name):
                    ##debug("%r matches %r" % (item,column_name))
                    return self[column_name]
            # Allow data["H,K,L"] -> 3 x Ncol array
            if "," in item:
                names = item.split(",")
                from numpy import array 
                return array([self[n] for n in names])
            # Was the intent to add a new column?
            return self.new_column(self,item)
        # Allow data["H","K","L"] -> table with columns "H","K","L"
        if is_string_array(item): return self.subtable(item)
        raise ValueError,exception

    def __delitem__(self,item):
        """Called when 'del table[item]' is used.
        Extends the functionality of recarray, allowing deletion of data
        fields."""
        ##debug("table.__delitem__(%r)" % item)
        if self.has_column(item): self.delete_column(item); return

    def __setattr__(self,name,value):
        """Called when 'table.name = value' is used.
        Extends the functionality of recarray, allowing adding new data fields.
        If 'value' is an array a new column is added.
        Else value is added as a property."""
        ##debug("table.__setattr__(%r)" % name)
        if name in attributes: object.__setattr__(self,name,value); return
        if hasattr(table,name): recarray.__setattr__(self,name,value); return
        if isarray(value): self.assign_column(name,value); return
        recarray.__setattr__(self,name,value)

    def __getattribute__(self,name):
        """Called for 'table.name' is used.
        Extends the functionality of recarray, allowing adding new columns."""
        ##debug("table.__getattribute__(%r)" % name)
        if name in attributes: return object.__getattribute__(self,name)
        try: return adjust_type(recarray.__getattribute__(self,name))
        except AttributeError: pass
        for column_name in self.columns:
            if matches(name,column_name):
                ##debug("%r matches %r" % (name,column_name))
                return getattr(self,column_name)
        # Allow HKL for a 2D array consisting of the columns H,K, and L.
        if len(name)>1 and all([n in self.columns for n in name]):
            ##debug("Treating %r as a composite column" % name)
            from numpy import array
            return array([getattr(self,n) for n in name])
        # Allow "I_SIGI" for a 2D array consisting of the columns I and SIGI.
        if "_" in name:
            names = name.split("_")
            if len(names)>1 and all([n in self.columns for n in names]):
                ##debug("Treating %r as a composite column" % name)
                from numpy import array
                return array([self[n] for n in names])
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError("table has no attribute %r" % name)
        if name.startswith("_"):
            raise AttributeError("table has no attribute %r" % name)
        # Was the intent to add a new column?
        return self.new_column(self,name)

    def __delattr__(self,name):
        """Called of 'del table.col' is used.
        Extends the functionality of recarray, allowing deletion of data
        fields."""
        ##debug("table.__delattr__(%r)" % name)
        if self.has_column(name): self.delete_column(name); return
        try: recarray.__delattr__(self,name)
        except AttributeError: pass 

    class new_column:
        """This is to handle a statements like 'x = data.XDET[0]' and
        'data.XDET[0] = 1' for a table named 'data' that does not yet have a
        column named 'XDET'. The first statement should assign a value of 'nan'
        to 'x', adding a new columns names 'XDET' to 'data'.
        The should add a new columns name 'XDET' to 'data', with the first
        element set to '1' and the other elemenrts to 'nan'.
        Python will first call the the '__getattr__' method of the 'table' class
        in both cases. Then, take the return value of '__getattr__' and call
        its '__getitem__' method in the first case or its '__setitem__' method
        in the second case.
        This means that the decision of whether or not to add a new column
        need to be made by the object returned by the '__getattr__'
        of 'table'. Normally this is an 'ndarray' object. 'new_column' is
        an extension of 'ndarray' with this capability added.
        """
        def __init__(self,table,name):
            from numpy import nan,zeros
            self.table = table
            self.name = name
            self.content = zeros(table.shape)+nan

        def __getattr__(self,attr):
            ##debug("table.new_column.__getattr__(%r)" % attr)
            if attr == "__setitem__": self.table.add_column(self.name)
            if not self.name in self.table.columns:
                return getattr(self.content,attr)
            return getattr(self.table[self.name],attr)


def split(s,separator=None):
    """'this is "a test"' -> ['this', 'is', 'a test']"""
    if separator is None:
        from shlex import split
        return split(s)
    else: return s.split(separator)

def isarray(x):
    """Is x an array-like object? numpy array, list or tuple"""
    if not hasattr(x,"__len__"): return False
    if issubclass(type(x),basestring): return False
    return True

def is_string_array(x):
    """Are the contents of 'x' strings?"""
    ##if hasattr(x,"dtype") and x.dtype.char == "S": return True
    return isarray(x) and len(x)>0 and isstring(x[0])

def array_dtype(a):
    """Element data type of an array or array-like object"""
    if hasattr(a,"dtype"): return a.dtype
    if not hasattr(a,"__len__"): return type(a)
    if len(a) == 0: return float
    # If 'a' is a list, it may contain element of different data type.
    # Converting it to an array, make numpy select a common data type that
    # is appropriate for all elements.
    from numpy import ndarray,array
    if not isinstance(a,ndarray): a = array(a)
    return a.dtype

def isstring(x):
    """Is x a string type or unicode string type object?"""
    return issubclass(type(x),basestring)

def istable(x):
    """Is x a string type or unicode string type object?"""
    if not hasattr(x,"dtype"): return False
    return x.dtype.descr[0][0] != ""

def adjust_type(x):
    """Convert array of strings to 'chararray' (as table.name would return.)
    and record arrays to table objects."""
    ##debug("adjust_type: type(x) = %r" % type(x))
    from numpy import issubdtype,chararray,ndarray
    # Make sure that coloumns containing strings are returned as chararray.
    if hasattr(x,"dtype") and issubdtype(x.dtype,str): x = x.view(chararray)
    # Convert record arrays to "table" objects.
    if type(x) == ndarray and x.dtype.descr[0][0] != "": x = x.view(table)
    return x

def matches(name,column_name):
    """Does a given name match the column name?"""
    if name == "": return False
    if name == column_name: return True
    # Strip off trailing unit, e.g. "[deg]", "[mm]", "/deg", "/mm".
    column_name = column_name.split("[")[0].strip()
    column_name = column_name.split("/")[0].strip()
    special_chars = " `~!@#$%^&*()-+=:;\"'[]{}|\\,.<>/?"
    for c in special_chars: column_name = column_name.replace(c,"_")
    if name.upper() == column_name.upper(): return True
    return False

def make_shape_compatible(array,shape):
    """Resize array so that it cam be broadcast to the shape 'shape'"""
    from numpy import ndarray,nan
    old_shape = array.shape
    new_shape = compatible_shape(array.shape,shape)
    new_array = ndarray(new_shape,array.dtype)
    erase(new_array)
    common_range = []
    for i in range(0,len(new_shape)):
        n = min(old_shape[-1-i],new_shape[-1-i])
        common_range = [slice(0,n)] + common_range
                    
    new_array[common_range] = array[common_range]
    return new_array

def compatible_shape(shape1,shape2):
    """Find the smallest shape larger than shape1 that can be broadcast
    to shape2"""
    shape = []
    n = min(len(shape1),len(shape2))
    for i in range(0,n):
        if shape1[-1-i] == 1: shape = [1]+shape
        else: shape = [shape2[-1-i]]+shape
    return tuple(shape)

def common_shape(shape1,shape2):
    """Find the smallest shapes such that shape2 that can be broadcast
    to shape1.
    Return value: pair of tuples"""
    from numpy import array,where,maximum
    ndim1,ndim2 = len(shape1),len(shape2)
    shape1,shape2 = list(shape1),list(shape2)
    while len(shape1) < len(shape2): shape1 = [1]+shape1
    while len(shape2) < len(shape1): shape2 = [1]+shape2
    shape1,shape2 = array(shape1),array(shape2)
    shape1 = maximum(shape1,shape2)
    shape2 = where(shape2 == 1,1,maximum(shape1,shape2))
    while shape1[0] == 1 and len(shape1) > ndim1: shape1 = shape1[1:]
    while shape2[0] == 1 and len(shape2) > ndim2: shape2 = shape2[1:]
    return tuple(shape1),tuple(shape2)

def resize_array(array,new_shape):
    """Change the size of an array, initializing new elements with default
    values.
    a: array to resize
    new_shape: new dimesions as tuple
    new_shape: new (larger) dimensions of array 'a'
    Return value: expanded version of array 'a'"""
    from numpy import all,ndarray
    if all(array.shape == new_shape): return array
    ##debug("resize_array: resizing from %r to %r" % (array.shape,new_shape))
    old_shape = array.shape
    new_array = ndarray(new_shape,array.dtype)
    erase(new_array)
    common_range = []
    for i in range(0,len(new_shape)):
        n = min(old_shape[-1-i],new_shape[-1-i])
        common_range = [slice(0,n)] + common_range
    new_array[common_range] = array[common_range]
    return new_array

def erase(a):
    """Fill the array 'a' with a default value for its data type.
    (0 for int, nan for float, empty string for string)"""
    from numpy import nan
    dtype = a.dtype.descr[0][1]
    if "f" in dtype: a.fill(nan)
    elif "i" in dtype: a.fill(0)
    elif "S" in dtype: a.fill("")

def concatenate(tables):
    """Merge serveral tables into one.
    tables: list of table objects
    return value: table object"""
    # Numpy's "concatente" will fail is both tables do not have the same data
    # type.
    from numpy import concatenate
    return concatenate(tables_with_same_columns(tables)).view(table).copy()
    
def tables_with_same_columns(tables_in):
    """
    tables_in: list of tables
    Return value: list of tables"""
    if have_same_columns(tables_in): return tables_in
 
    dtype = common_dtypes(tables_in)
    tables_out = []
    for i in range(0,len(tables_in)):
        ##status("Reordering columns",i/len(tables_in))
        table_in = tables_in[i]
        ##debug ("dtypes=%r" % dtypes)
        from table import table as Table
        table_out = Table(rows=table_in.shape,dtype=dtype)
        for column in table_in.columns: table_out[column] = table_in[column]
        table_out.filename = table_in.filename
        tables_out += [table_out]
    return tables_out

def make_dtype_compatible(data,data2):
    """Make sure that data has all the columns columns data2 has too.
    data: table, input
    data2: table
    Return value: table"""
    if not istable(data) or not istable(data2): return data
    if data.dtype == data2.dtype: return data
 
    dtype = common_dtypes([data,data2])
    data_out = table(rows=data.shape,dtype=dtype)
    for column in data.columns: data_out[column] = data[column]
    data_out.filename = data.filename
    return data_out

def common_dtypes(tables_in):
    """
    tables_in: list of tables
    Return value: list of tuples (string,dtype)"""
    if have_same_columns(tables_in): return tables_in
    
    # Find common columns.
    dtype_dict = OrderedDict()
    for table_in in tables_in:
        for column in table_in.columns:
            dtype = table_in[column].dtype
            if not column in dtype_dict: dtype_dict[column] = dtype
            else: dtype_dict[column] = common_dtype(dtype_dict[column],dtype)
    columns,dtypes = dtype_dict.keys(),dtype_dict.values()
    dtype = zip(columns,dtypes)
    return dtype

def common_dtype(dtype1,dtype2):
    """The data type that can represent objects or both 'dtype1' and
    'dtype2' without loss of precision.
    E.g. (int,float64) -> float64, ('S20','S26') -> 'S26'"""
    from numpy import dtype
    # Make sure data types are numpy data types.
    dtype1,dtype2 = dtype(dtype1),dtype(dtype2)
    if dtype1.kind == dtype2.kind:
        return dtype1 if dtype1.itemsize > dtype2.itemsize else dtype2
    if dtype1.kind == "S": return dtype1
    if dtype2.kind == "S": return dtype2
    if dtype1.kind == "f": return dtype1
    if dtype2.kind == "f": return dtype2
    if dtype1.kind == "i": return dtype1
    if dtype2.kind == "i": return dtype2

def have_same_columns(tables):
    """Do all tables have the same columns, in the same order?
    hklset: list of tables
    Return value: True or False"""
    return all([table.dtype == tables[0].dtype for table in tables[1:]])

def unique(a):
    """A shorter version of th earray a without redundent elecements,
    in the order of thier first occurance"""
    from numpy import atleast_1d,array
    a = atleast_1d(a)
    b = []
    for x in a:
        if not x in b: b += [x]
    return array(b,dtype=a.dtype).view(type(a))

def samerow(a):
    """Are all rows of the array 'a' the same?
    a: 2D array"""
    from numpy import all
    return all([all(a[0] == a[i]) for i in range(0,len(a))])

def tostr(value):
    """Convert value to a string in a portable, system-independent way"""
    from numpy import isnan,isinf,isinf
    if isinstance(value,basestring): return value
    elif isnan(value): return "nan"
    elif isinf(value) and value>0: return "inf"
    elif isinf(value) and value<0: return "-inf"
    return "%g" % value

def asstr(value):
    """Represent a unicode string as a UTF-8 encoded 8-bit string"""
    import codecs
    return codecs.encode(value,"utf-8")

def UNIX_text(text):
    """Convert line breaks from DOS/Windows or Macintosh to UNIX convention.
    DOS/Windows: '\n\r', Macinosh: '\r':, UNIX: '\n'"""
    if not "\r" in text: return text # already in UNIX format
    text = text.replace("\n\r","\n") # was DOS to UNIX
    text = text.replace("\r\n","\n") # was ? to UNIX
    text = text.replace("\r","\n") #  MAC to UNIX
    return text

def file_timestamp(filename):
    """Modification time in seconds since 1 Jan 1970 0:00 UT
    filename: string or array or strings
    return value: float or float array"""
    if not isarray(filename):
        from os.path import exists,getmtime
        if exists(filename): return getmtime(filename)
        else: return 0.0
    else:
        from numpy import array
        return array([file_timestamp(f) for f in filename])

def filesize(filename):
    """Length of a file in bytes (0 if the file does not exists).
    filename: string or array or strings
    return value: int or int array"""
    if not isarray(filename):
        from os.path import exists,getsize
        if exists(filename): return getsize(filename)
        else: return 0
    else:
        from numpy import array
        return array([filesize(f) for f in filename])


if __name__ == "__main__": # example for testing
    import logging; logging.basicConfig(level=logging.DEBUG)
    from pdb import pm
    filename = "//Femto/C/All Projects/APS/Experiments/2013.03/Analysis/Laue/"\
        "PYP/PYP-E46Q-H/PYP-E46Q-H1-288K/PYP-E46Q-H1-288K.log"
    from configurations import parameters
    self = table(text=parameters)
    name = "choices"
    ##print('data = table(filename,separator="\\t")')
    print('self[%r]' % name)
    print('self.%s' % name)
