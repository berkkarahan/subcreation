# special thanks to Solian <3

BitsPerChar = 6

def MakeBase64ConversionTable():
    base64ConversionTable = {0: 'A'}
    i = 0
    for num in range(0, 26):
        base64ConversionTable[i] = chr(65 + num)
        i += 1

    for num in range(0, 26):
        base64ConversionTable[i] = chr(97 + num)
        i += 1

    for num in range(0, 10):
        base64ConversionTable[i] = str(num)
        i += 1

    base64ConversionTable[i] = '+'
    i += 1
    base64ConversionTable[i] = '/'
    return base64ConversionTable


NumberToBase64CharConversionTable = MakeBase64ConversionTable()
Base64CharToNumberConversionTable = {v: k for k, v in MakeBase64ConversionTable().items()}


def ConvertToBase64(dataEntries):
    exportString = ""
    currentValue = 0
    currentReservedBits = 0
    totalBits = 0

    for i, dataEntry in enumerate(dataEntries):
        remainingValue = dataEntry.value
        remainingRequiredBits = dataEntry.bitWidth
        maxValue = 1 << remainingRequiredBits
        if remainingValue >= maxValue:
            print("Data entry has higher value than storable in bitWidth. (%d in %d bits)".format(remainingValue, remainingRequiredBits))
            return ""

        totalBits = totalBits + remainingRequiredBits
        while remainingRequiredBits > 0:
            spaceInCurrentValue = (BitsPerChar - currentReservedBits)
            maxStorableValue = 1 << spaceInCurrentValue
            remainder = remainingValue % maxStorableValue
            remainingValue = remainingValue >> spaceInCurrentValue
            currentValue = currentValue + (remainder << currentReservedBits)

            if spaceInCurrentValue > remainingRequiredBits:
                currentReservedBits = (currentReservedBits + remainingRequiredBits) % BitsPerChar
                remainingRequiredBits = 0
            else:
                exportString += NumberToBase64CharConversionTable[currentValue]
                currentValue = 0
                currentReservedBits = 0
                remainingRequiredBits = remainingRequiredBits - spaceInCurrentValue


    if currentReservedBits > 0:
        exportString += NumberToBase64CharConversionTable[currentValue]

    return exportString


def ConvertFromBase64(exportString):
    dataValues = {}
    for i in range (0, len(exportString)):
        dataValues[i] = Base64CharToNumberConversionTable[exportString[i:i+1]]

    return dataValues

