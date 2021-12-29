# Daily Notes

A project for organizing daily notes. It creates a folder and file structure dependent on time. Something like:
``` 
TODO: Get an example file structure
```

The idea is to be able to write something quick while not sacrificing organization.
In that way, you can easiliy get back to your notes later.

### Running the script
You can call python with the script
``` console
python main.py [argument]
```
Or you can execute it like this
``` console
./main.py [argument]
```

The **[argument]** is the target directory to store your notes. Directories for years and files for months, that's the structure.
On each file you'll get specific headers for the current DAY and the current WEEK.

Currently the support is meant for [**vim**](https://en.wikipedia.org/wiki/Vim_(text_editor)), some of the features may not work on other editors. Vim will place you in the exact position of the file for the current day... you just start typing.