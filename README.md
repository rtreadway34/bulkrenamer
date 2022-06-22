# Bulk File Renamer

**VERSION: 1.0 - "It works lol" edition**

A simple immature file renamer proof-of concept, handles renaming by method of case or character.  It was built from scratch without referencing existing file rename programs.

Changing the case of filenames excludes extensions and is chosen from  lowercase, uppercase or titlecase.

Regarding characters, it is a one-to-one character substitution.  The program accounts for any single character to target or use for substitution.

This is a first "big" project, from the perspective of a beginner.  Lots of comments and an attempt was made to make the code more readable.  Plenty of room for refactoring and expansion, for later fun.

### Modules Used

All built-ins

- sqlite3
- os
- subprocess
- time
- re
- shutil

---

# METHODS

### \_\_init\_\_()

Initializes a sqlite3 db in memory for file data collection, then sets up a table with pertinent file info targets:

- id - auto incrementing id #
- pathname - full path + filename + extension
- filename - filename + extension
- name - filename only
- path - filepath
- extension - 3-4 char extension after last '.', IF there is one
- type - file type
- size - file size in Bytes
- atime, mtime, ctime - access, modify & created times

The db initialization process is set in a try/except clause to account for possible errors in db instantiation and in table creation

### \_\_collectFile\_\_()

Internal method to parse files in a dir and collect information about them into a db for further processing

**Takes:** path where target files are contained

**Returns:** Nothing

Uses enumerate(os.listdir(path)) to collect both the current file count and the filename itself. Within this loop, we set up to collect the desired data points for each file.

Used try/except/else for extension parsing, since files without an extension would return an error when attempting to get the index of the last dot w/ .rindex().  Errors set extension to None, and successes are passed to the else block for processing the extension and the 'name' of the file (without extension)

File type is obtained using subprocess.run() and passing in the linux 'file' cmd to get the MIME type of the file (bc simpler definition of the type). Output is then parsed to get ONLY the simple type text. *NOTE: This means program isn't compatable w/ Windows, so will have to account for that*

For the other attributes, used os.stat() per file to return an stat object where individual attribs could be read & assigned to vars.

Internal function 'readabletime' used to convert each time (a,m,c) to a human readable format.

Finally, the values obtained are inserted into the db

### \_\_changeCase\_\_()

Internal method to change the case of given files.

**TAKES:** cs='case', choices btwn title|lower|upper cases

**RETURNS:** a dict whose k:v are {originalFilename : newFilename}

First, Selects name & extension from catalogue, then uses list comprehensions to parse names & extensions into 2 separate lists (better for readability)

Loops over range of filenames, first checking the 'cs' value for what case to apply, applies it and enters each as the values for each k/v pair in the output dict (see RETURNS above).  Raises error if 'cs' value is NOT from accepted 3 types.

This output is meant to be passed to the \_\_renamer\_\_() method for the actual renaming using the new values.

### \_\_changeChar\_\_()

Internal method to change characters in a file

**TAKES:**

- repl - the new value to sub in
- target - what to target for replacement
- igncs - "ignore case" (*not implemented yet*)

**RETURNS:** a tuple containing an output dict (like in \_\_changeCase\_\_()) and the target & repl originally passed in, so they can be utilized in \_\_renamer\_\_()

**NOTE: only repl is used thus far. Is there a need for target in renamer()?**

First, Selects name & extension from catalogue, then uses list comprehensions to parse names & extensions into 2 separate lists (better for readability)

Then loops over number of files.  In the loop regex and "overtarget" regex are initialized w/ target and utilizing repl, respectively (**This could prob be moved outside the loop**).

Next, regex is used to *sub* the file's name, the result of which is set to temp var 'build'.

Next, we compile the 'overtarget' regex, which will be used to catch "more than expected" replacements in a row of a subbed file.

Using this compiled 'overtarget' regex, check whether build contains "more than expected".  If it does, replace the "more than expected" group of chars with the original replace string, and put that as the output dict value for the file.  Otherwise just use 'build' as the value.

The returned output dict is to be used as input to the \_\_renamer\_\_() method, so it can do the real renaming using what was processed.  Target & repl are returned as well to be used as needed.

**NOTE: At this point only repl is used in renamer**

### \_\_sqlq\_\_()

An internal method to test db queries pertinent to the program.  For debugging, but the query customization may be able to be implemented somewhere else.  The indended use was to collect other data for already parsed files, selecting said data from the db based on the original file names.  This targeted selection would allow construction of full pathnames for the files to actually rename (which os.rename() requires)

**TAKES:**

- query - the actual SQL query, in this case *only* with SELECT and FROM clauses and no filters (since filter WHERE would be added on inside the method).
- inp - the input data, taken from either changeCase or changeChar

**RETURNS:** Nothing, but prints the fetchall result

Since inputs from changeCase & changeChar are dicts, we use .keys() to get the *original* filenames, and set that to a var.

Then, loop over that list, passing the filename into a query-modifier var that leverages string .format().  Used WHERE

Finally, the query is executed and the fetched data printed (for each file).  This functionality will probably be modified to RETURN a list of pathnames for each file to be renamed.

### \_\_renamer\_\_()

Internal method meant to do the actual renaming of the files.

**TAKES:** input tuple from changeChar or dict from changeCase

**RETURNS:** Nothing yet, but prob should return a status string or some shit

First, checks the type of the input to ensure it's a compatable tuple or dict.

IF TUPLE, divides the elements into separate vars (for readability).  Then, iterates over the dict.items() and checks whether the original filename == the new filename (so we can skip renaming the files who have no changes queued)

IF DICT, does the latter since no tuple to divide up.

Final step for each is to implement the actual renaming, making sure to prepend the path to each filename before passing it to os.rename(original, new)

### fileRename()

The public method allowing selection of various parameters to control internal methods.

**TAKES:**

- method - choosing between 'case' or 'char' to call their respective functions. Default = 'case'
- path - not sure if used
- tcase - "target case", between title|lower|upper, which is passed to changeCase() method
- tgt - the replacement target, passed to changeChar() method
- repl - the substitution material, to replace 'tgt', passed to changeChar() method

**RETURNS:** Nothing, just calls internal methods as needed all the way up to the actual renaming

First, checks 'method' value.  An exception clause is ready to catch incorrect values.

Second, for each if/elif block, a try/except/else block is used to test for existence of 'tcase' value for method='case', and *both* the 'tgt' and 'repl' value for method='char'.  Detailed exception messages if values missing or are shit.

IF the values check out, then call \_\_renamer\_\_().  Depending on the 'method', the related internal method is passed in as the argument to renamer(), with the appropriate args passed into that method.

**This will alter filenames! Should implement a proposed changes list for user, and prompt to confirm changes to avoid accidents**

# USAGE

**Create class instance object**, passing target path as the arg.

Target path should contain only the files to rename

>> import bulkrenamer

>> v = bulkrenamer.Catalogue('./path')


**Call fileRename method:**

>> v.fileRename(method='case',cpath=None,tcase=None,tgt=None,repl=None)

- *method:* 'case'|'char'
- *cpath:* custom output path
- *tcase:* if method='case', 'title'|'lower'|'upper'
- *tgt,repl:* if method='char', single characters representing "what to target for replacement" and "what to replace with", respectively

---

## Future Ideas

- the use of subprocess.run() and the **linux** file program.  Need a reimplementation to make compat w/ windows.
- fileRename() method (or wherever this functionality makes sense to insert) needs a way to halt before implementing changes, first showing proposed changes and then querying the user to accept changes (input should be able to handle the halting and control the behavior thereafter)
