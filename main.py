#!/bin/python

# This version currently does the following:
# - Use sys.argv to get the directory for the notes
# - If there's no "notesconfig.yml" file, create one based on template
# - Get current time (or hardcoded times for testing) and generates a
#   folder and a file for you to type your notes.
# 
# The notes follow the pattern:
# - A directory/folder for the year (ex: 2020, 2021)
# - A file for the month based on current language
#   (ex: November.md [en-US], Novembro.md [pt-BR])
# - An H1 for the current week (with emoji) (configurable on notesconfig.yml)
# - An H2 for the current day (with emoji) (configurable on notesconfig.yml)
#
#
# TODO
# - Refactor into multiple files

from typing import Optional, Callable, List, Tuple
import sys
import os
import shutil
import re
import yaml

import datetime
Datetime = datetime.datetime

class DocumentFormatter:

    def __init__(self, parsedObj):
        self.parsedObj = parsedObj

    def getFromYaml(filePath: str) -> None:
        try:
            with open(filePath, "r") as yamlFile:
                parsedObj = yaml.safe_load(yamlFile)
                return DocumentFormatter(parsedObj)
        except error:
            print(error)

    def mainHeader(self) -> str:
        return self.parsedObj["main"]["header"]

    def mainFooter(self) -> str:
        return self.parsedObj["main"]["footer"]

    def weekHeader(self) -> str:
        return self.parsedObj["week"]["header"]

    def dayHeader(self) -> str:
        return self.parsedObj["day"]["header"]

    def weekDayEmojis(self) -> List[str]:
        return self.parsedObj["emojis"]["week"]

    def weekParserString(self) -> str:
        return self.parsedObj["week"]["parser"]

    def weekParserOffset(self) -> int:
        return self.parsedObj["week"]["parserOffset"]

    def dayParserString(self) -> str:
        return self.parsedObj["day"]["parser"]

    def dayParserOffset(self) -> int:
        return self.parsedObj["day"]["parserOffset"]

    def formatMainHeader(self, time: Datetime) -> str:
        return DocumentFormatter.stringFormatWithTime(time, self.mainHeader())

    def formatMainFooter(self, time: Datetime) -> str:
        return DocumentFormatter.stringFormatWithTime(time, self.mainFooter())

    def customFormat(self, string: str, currentDate: Datetime) -> Optional[str]:
        if(string == "weekDayEmoji"):
            return self.weekDayEmojis()[currentDate.weekday()]

        return None

    def parseDocument(self, filePath: str):
        with open(filePath, "r") as file:
            lines = file.readlines()

        parseResult = {
            "weeks": DocumentFormatter.parseLines(lines, self.weekParserString(), self.weekParserOffset()),
            "days": DocumentFormatter.parseLines(lines, self.dayParserString(), self.dayParserOffset()),
            "lines": lines
        }

        return parseResult

    def parseLines(lines: List[str], parserString: str, parserOffset: int):
        elements = []

        for index, line, in enumerate(lines):
            location = line.find(parserString)
            if(location != -1):
                targetLineIndex = parserOffset + index
                if(targetLineIndex < len(lines) and targetLineIndex >= 0):
                    targetLine = lines[targetLineIndex]

                    numbersInLine = re.findall(r'\d+', targetLine)
                    if(len(numbersInLine) > 0):
                        element = {
                            "data": int(numbersInLine[0]),
                            "line": targetLineIndex
                        }
                        elements.append(element)

        return elements

    def formatContent(self, datetime: Datetime, content: str) -> str:
        return DocumentFormatter.stringFormatWithTime(datetime, content, self.customFormat)

    def stringFormatWithTime(datetime: Datetime, formatString: str, customFormat: Callable[[str, Datetime], Optional[str]] = None) -> str:
        """ Replaces {things} inside curly brakets with a formatted string

            If there is a customFormat function passed as an argument, that
            function will be called first to format the string. If it returns
            None, then the default formatting with datetime.strftime(...) will
            be used instead. """
        result = ""
        index = 0
        startIndex = 0

        while(index < len(formatString)):
            if(formatString[index] == "{"):
                result += formatString[startIndex: index]
                startIndex = index + 1

            if(formatString[index] == "}"):
                parsedString = formatString[startIndex: index]

                customResult = None
                if (customFormat != None):
                    customResult = customFormat(parsedString, datetime)

                if (customResult != None):
                    result += customResult
                else:
                    result += datetime.strftime(parsedString)

                startIndex = index + 1

            index += 1

        result += formatString[startIndex:]
        return result

class LineBlock:
    def __init__(self, lines: List[str]):
        self.lines = lines

    def __len__(self):
        return len(self.lines)

    def __repr__(self):
        return "Block({})".format(self.lines)


class WeekBlock(LineBlock):
    def __init__(self, data: int, lines: List[str]):
        self.data = data
        super().__init__(lines)

    def __repr__(self):
        return "Week<{}>({})".format(self.data, self.lines)


class DayBlock(LineBlock):
    def __init__(self, data: int, lines: List[str]):
        self.data = data
        super().__init__(lines)

    def __repr__(self):
        return "Day<{}>({})".format(self.data, self.lines)


class DocumentParser:
    def __init__(self, documentFormatter: DocumentFormatter):
        self.documentFormatter = documentFormatter

    def parse(self, filePath: str) -> List[LineBlock]:
        def trimBreakLine(l): return l if(l[-1] != "\n") else l[:-1]
        with open(filePath, "r") as file:
            lines = list(map(trimBreakLine, file.readlines()))

        headerLength = self.documentFormatter.mainHeader().count('\n')
        headerBlock = LineBlock(lines[:headerLength])
        footerLength = self.documentFormatter.mainFooter().count('\n')
        footerBlock = LineBlock(lines[-footerLength:])

        middleLines = lines[headerLength:-footerLength]

        lineBlocks = [headerBlock]
        lineBlocks += self.getWeekAndDayBlocks(middleLines)
        lineBlocks += [footerBlock]

        return lineBlocks

    def getWeekAndDayBlocks(self, lines: List[str]):
        result: List[LineBlock] = []
        lastBlock: LineBlock = None
        lastBlockStart: Optional[int] = None

        for index, line in enumerate(lines):
            isWeekHeader = (
                line.find(self.documentFormatter.weekParserString()) != -1)
            isDayHeader = (
                line.find(self.documentFormatter.dayParserString()) != -1)
            isHeader = isWeekHeader or isDayHeader
            if(not isHeader):
                continue

            if(isWeekHeader):
                parserOffset = self.documentFormatter.weekParserOffset()
            else:
                parserOffset = self.documentFormatter.dayParserOffset()

            headerTop = parserOffset + index
            headerData = DocumentParser.getHeaderData(headerTop, lines)

            if(lastBlock != None and lastBlockStart != None):
                lastBlock.lines = lines[lastBlockStart:headerTop]
                result.append(lastBlock)

            if(isWeekHeader):
                lastBlock = WeekBlock(headerData, [])
            else:
                lastBlock = DayBlock(headerData, [])
            lastBlockStart = headerTop

        # Reach end of lines and must finish remaining block
        if(lastBlock != None and lastBlockStart != None):
            lastBlock.lines = lines[lastBlockStart:]
            result.append(lastBlock)

        return result

    def getHeaderData(targetLineIndex: int, lines: List[str]):
        numbersInLine = re.findall(r'\d+', lines[targetLineIndex])
        return int(numbersInLine[0])

class FileManager:
    def createFileGetBlocks(time: Datetime, documentFormatter: DocumentFormatter):
        # Create year dir
        attemptCreateYearDir(time.year)
        yearPath = str(time.year)

        noteFileName = getTimeFileName(time)
        noteFullPath = os.path.join(yearPath, noteFileName)
        exists = os.path.isfile(noteFullPath)

        if(not exists):
            with open(noteFullPath, "w") as file:
                file.write(documentFormatter.formatMainHeader(time))
                file.write("\n")
                file.write(documentFormatter.formatMainFooter(time))

        parser = DocumentParser(documentFormatter)
        lineBlocks = parser.parse(noteFullPath)
        return lineBlocks, noteFullPath

    def insertHeaderBlocksAndGetIndexToEdit(blocks: List[LineBlock], time: Datetime, documentFormatter: DocumentFormatter) -> Tuple[List[LineBlock], int]:
        currentWeekNumber = int(time.strftime("%U"))
        currentDay = time.day
        weekBlockIndex = FileManager.getWeekBlockIndex(
            blocks, currentWeekNumber)
        dayBlockIndex = FileManager.getDayBlockIndex(blocks, currentDay)

        if(weekBlockIndex != None and dayBlockIndex != None):
            # Position already exists
            return blocks, dayBlockIndex

        if(weekBlockIndex != None and dayBlockIndex == None):
            # Should create dayHeader
            dayBlock = FileManager.createDayHeader(time, documentFormatter)
            endOfWeekBlockIndex = weekBlockIndex + 1
            for index in range(weekBlockIndex + 1, len(blocks)):
                if(type(blocks[index]) == DayBlock):
                    continue
                endOfWeekBlockIndex = index
                break

            newBlocks = blocks[:endOfWeekBlockIndex] + \
                [dayBlock] + blocks[endOfWeekBlockIndex:]
            return newBlocks, endOfWeekBlockIndex

        if(weekBlockIndex == None and dayBlockIndex != None):
            # Weird and a little inconsistent scenario
            pass

        # else ->
        # If there is no week and no day header for currentDay
        weekBlock = FileManager.createWeekHeader(time, documentFormatter)
        dayBlock = FileManager.createDayHeader(time, documentFormatter)

        lastWeekIndex = 0
        for index, block in enumerate(blocks):
            if((type(block) == WeekBlock) and block.data < currentWeekNumber):
                lastWeekIndex = index

        endOfWeekBlockIndex = lastWeekIndex + 1
        for index in range(lastWeekIndex + 1, len(blocks)):
            if(type(blocks[index]) == DayBlock):
                continue
            endOfWeekBlockIndex = index
            break

        newBlocks = blocks[:endOfWeekBlockIndex] + \
            [weekBlock, dayBlock] + blocks[endOfWeekBlockIndex:]
        return newBlocks, endOfWeekBlockIndex + 1

    def getWeekBlockIndex(lineBlocks: List[LineBlock], weekNumber: int) -> Optional[int]:
        for index, block in enumerate(lineBlocks):
            if(type(block) == WeekBlock and block.data == weekNumber):
                return index
        return None

    def getDayBlockIndex(lineBlocks: List[LineBlock], dayNumber: int) -> Optional[int]:
        for index, block in enumerate(lineBlocks):
            if(type(block) == DayBlock and block.data == dayNumber):
                return index
        return None

    def createWeekHeader(time: Datetime, documentFormatter: DocumentFormatter) -> LineBlock:
        currentWeekNumber = int(time.strftime("%U"))
        thisWeekHeader = documentFormatter.formatContent(
            time, documentFormatter.weekHeader()).split('\n')
        return WeekBlock(currentWeekNumber, thisWeekHeader)

    def createDayHeader(time: Datetime, documentFormatter: DocumentFormatter) -> LineBlock:
        currentDay = time.day
        thisDayHeader = documentFormatter.formatContent(
            time, documentFormatter.dayHeader()).split('\n')
        return DayBlock(currentDay, thisDayHeader)

    def writeFileAndGetEditPoint(fileName: str, blocks: List[LineBlock], blockIndexToEdit: Optional[int]) -> Optional[int]:
        linesSoFar = 0
        lineToEdit = None

        with open(fileName, "w") as file:
            for index, block in enumerate(blocks):
                for line in block.lines:
                    file.write(line + "\n")
                linesSoFar += len(block)
                if(index == blockIndexToEdit):
                    lineToEdit = linesSoFar
                    # Add one more line after edit so it's better to type
                    file.write("\n")
        
        return lineToEdit


DEFAULT_CONFIG_FILE = "notesconfig.yml"
DEFAULT_TEMPLATE_CONFIG_FILE = "templates/daily-notes.yml"

def main():
    rootDir = getRootDirFromArgs()
    moveToRootDir(rootDir)
    attemptCreateConfigFile()
    documentFormatter = DocumentFormatter.getFromYaml(DEFAULT_CONFIG_FILE)

    currentTime = Datetime.now()

    timeTests = [
        currentTime,
        # Datetime(2021, 11, 15),
        # Datetime(2021, 11, 16),
        # Datetime(2020, 1, 15),
        # Datetime(2020, 1, 5),
    ]

    for time in timeTests:
        blocks, noteFilePath = FileManager.createFileGetBlocks(time, documentFormatter)
        newBlocks, blockIndexToEdit = FileManager.insertHeaderBlocksAndGetIndexToEdit(
            blocks, time, documentFormatter)
        lineToEdit = FileManager.writeFileAndGetEditPoint(noteFilePath, newBlocks, blockIndexToEdit)
        
        input("Added entry for time [{}], let's edit?".format(time))
        os.system("${EDITOR:-vim} +" + str(lineToEdit) + " " + noteFilePath)

    return

def getRootDirFromArgs() -> str:
    if (not checkValidArguments()):
        print("ERROR: too few arguments. Please specify a directory for the notes journal")
        exit(1)

    rootDir = sys.argv[1]
    if (not os.path.isdir(rootDir)):
        print("ERROR: The path '{}' is not a valid directory".format(rootDir))
        exit(1)
    return rootDir

def moveToRootDir(rootDir: str):
    os.chdir(rootDir)

def checkValidArguments():
    return len(sys.argv) >= 2

def attemptCreateConfigFile():
    dirname = os.path.dirname(__file__)
    templateConfigFile = os.path.join(dirname, DEFAULT_TEMPLATE_CONFIG_FILE)

    if (not os.path.isfile(DEFAULT_CONFIG_FILE)):
        shutil.copyfile(templateConfigFile, DEFAULT_CONFIG_FILE)

def attemptCreateYearDir(year: int):
    if(not os.path.isdir(str(year))):
        os.mkdir(str(year))

def getTimeFileName(time: Datetime, extension: str = ".md"):
    # Month locale full name
    return time.strftime("%B") + extension

if __name__ == "__main__":
    main()
