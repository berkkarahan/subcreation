# special thanks to Solian <3

import ExportUtil

Object = lambda **kwargs: type("Object", (), kwargs)()


class ExportDataStream:
    def __init__(self):
        self.dataEntries = []

    def AddValue(self, bitWidth, value):
        self.dataEntries.append(Object(bitWidth=bitWidth, value=value))

    def GetExportString(self):
        return ExportUtil.ConvertToBase64(self.dataEntries)


