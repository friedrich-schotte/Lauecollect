class Member(object):
    def __init__(self, identifier):
        self.identifier = identifier
        print("Member __init__ " + self.identifier)

    def __del__(self):
        print("Member __del__ " + self.identifier)


class WithMembers(object):
    def __init__(self):
        print("WithMembers __init__")
        print(WithMembers.classMem)
        self.instanceMem = Member("instance mem")

    def __del__(self):
        print("WithMembers __del__")

    classMem = Member


if __name__ == "__main__":
    print("main")
    WithMembers()
    print("end")