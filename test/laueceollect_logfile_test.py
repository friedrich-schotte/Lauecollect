filename = '/data/anfinrud_1203/Data/Laue/PYP/PYP-H2/PYP-H2.log'
lines = file(filename).readlines()
column_headers = lines[18]
line1 = lines[19]
line2 = lines[20]
NF = [line.count("\t") for line in lines[18:]]
