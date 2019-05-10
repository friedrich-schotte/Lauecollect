"""Preceed error messages with timestamps
F. Schotte, Nov 13, 2016
"""
__version__ = "1.0"

def timestamp_error_messages():
    """Preceed error messages with timestamps"""
    import sys
    from datetime import datetime
    if not hasattr(sys.stderr,"messages"):
        old_f = sys.stderr
        class F:
            messages = ""
            def write(self, x):
                self.messages += x
                if "\n" in self.messages:
                    for message in self.messages.split("\n")[0:-1]:
                        old_f.write(str(datetime.now())[:-3]+" "+message+"\n")
                    self.messages = self.messages.split("\n")[-1]
        sys.stderr = F()


if __name__ == "__main__":
    timestamp_error_messages()
    timestamp_error_messages()
    import sys
    sys.stderr.write("x\ny\n")
    print "x","y"
