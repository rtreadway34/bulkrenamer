''' ***bulkrenamer***
    Bulk file cataloguer and manipulator framework
    **********************************************
Version: 1.0
Programmed by: Raf Treadway
****
Works well, but is strictly case sensitive for this version
Usage:
1. Create class instance object, passing target path as the arg.  Target path should contain only the files to rename
    >> import bulkrenamer
    >> v = bulkrenamer.Catalogue('./path')
2. Call fileRename method:  
    >> v.fileRename(method='case',cpath=None,tcase=None,tgt=None,repl=None)
        method -> 'case'|'char'
        cpath -> <custom output path>
        tcase -> if method='case', 'title'|'lower'|'upper'
        tgt,repl -> if method='char',
        these are "what to target for replacement" and "what to replace with", respectively
Background:  This is a first "big" project, from the perspective of a beginner.  Lots of comments and an attempt was made to make the code more readable.  Plenty of room for refactoring and expansion. 
'''
import sqlite3 as sql
from sqlite3 import Error
import os

class Catalogue:
    def __init__(self,tpath):
        self.tpath = tpath  # *Target path*, where the files are
        try:
            # Create & connect to tmp db in memory, then attempt to make a table 
            self.db = sql.connect(':memory:')
            self.crs = self.db.cursor()
            self.crs.execute('''CREATE TABLE IF NOT EXISTS catalogue(id SMALLINT UNSIGNED AUTO_INCREMENT, pathname TEXT NOT NULL, filename TEXT NOT NULL, name TEXT NOT NULL, path TEXT NOT NULL, extension TEXT, type TEXT, size INTEGER UNSIGNED NOT NULL, atime INTEGER UNSIGNED, mtime INTEGER UNSIGNED, ctime INTEGER UNSIGNED, PRIMARY KEY (id))''')
        except Error:
            print("db or table creation exception encountered")
            print(Error)
        
    def __collectFile__(self, path):
        import subprocess as s
        import time
        tot_file = 0   # tally number of files parsed
        for count, filename in enumerate(os.listdir(path)):
            tot_file += 1
            pathname = path+'/'+filename    # construct full path + filename + extension
            try:filename.rindex('.')
            except:
                extension = None    # when no '.' found
            else:
                ext_idx = filename.rindex('.')  # the last '.' probably indicates the extension
                extension = filename[ext_idx:].lstrip('.')
                filename_only = filename[:ext_idx].strip('.')   # file's name without extension
            # get filetype, using linux 'file', PY3.7+
            # WARN: Testing required: This is def incompatable with Windows, need to account for this for multi-system compatability
            v = s.run(['file','--mime-type', pathname], capture_output=True, text=True)
            ftype = v.stdout.split(':')[1].strip()
            # set up for file attrib get
            fattr = os.stat(path+'/'+filename)  # creates file stats object
            size = fattr.st_size    # in Bytes
            atime = fattr.st_atime  # access time
            mtime = fattr.st_mtime  # modified time
            ctime = fattr.st_ctime  # creation time
            # A simple formatter for the times, which were gathered in seconds since epoch
            times = [atime,mtime,ctime] 
            def readabletime(t):
                c = time.strptime(time.ctime(t))
                return time.strftime('%m-%d-%yT%R', c)
            tconv = list(map(readabletime, times))

            # INSERT INTO DB
            stmt = "INSERT INTO catalogue(pathname,filename,name,path,extension,type,size,atime,mtime,ctime)VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            vals = (pathname,filename,filename_only, path, extension, ftype, size, tconv[0], tconv[1], tconv[2])
            self.crs.execute(stmt,vals)
            
        print("Total files parsed:{}".format(tot_file)) # ux

    def __changeCase__(self,cs='title'):
        output = {} # k:v -> origName:newName
        self.crs.execute("SELECT name, extension from catalogue")
        files = self.crs.fetchall()
        names = [x[0] for x in files]   # comprehension selecting the 'name' from the SQL return
        exts = [x[1] for x in files]    # ditto for 'extension'
        for i in range(len(names)):
            tgt = names[i]+'.'+exts[i]  # build filename of current target
            if cs == 'title':
                build = names[i].title() +'.'+exts[i]
                output[tgt] = build
            elif cs == 'lower':
                build = names[i].lower() +'.'+exts[i]
                output[tgt] = build
            elif cs == 'upper':
                build = names[i].upper() + '.' + exts[i]
                output[tgt] = build
            else:
                raise KeyError("Bad case type.  Set arg 'tcase' to choice btwn title|lower|upper")  # Account for wrong choices / typos
        return output


    def __changeChar__(self,target=' ',repl='_',igncs=True):
        # target = what you're targeting TO replace
        # repl = what to replace WITH
        # ****************
        # Test for repl and target args, as they are required
        if repl == None:
            if target == None:
                raise Exception("Missing values for 'target' and 'repl'")
            else:
                raise Exception("Missing value for 'repl'")
        elif target == None:
            raise Exception("Missing value for 'target'")
        import re
        output = {}
        # Set of special chars that would need to be escaped to function with regex
        spchars =  [' ','.','^','$','-','[',']','(',')','|']
        # Get files info
        self.crs.execute("SELECT name, extension from catalogue")
        files = self.crs.fetchall()
        names = [x[0].rstrip() for x in files]
        exts = [x[1] for x in files]
        ### Init regex to seek target ###
        # If target is in special characters set, do special escaped regex
        if target in spchars:
            reg_rgx = re.compile("\{}".format(target))
        else: 
            reg_rgx = re.compile(target)
        ### Init "more than expected" regex to allow cleanup of multiple subs in a row ###
        # First, check if repl is empty string & set special regex for it
        if repl == '':
            ot_rgx = re.compile("<([a-zA-Z_0-9]*)>")
        # Next, check if repl is in special chars set & set special escaped regex
        elif repl in spchars:
            overtarget_rgx = "(\{})".format(repl)+"{2,5}"
            ot_rgx = re.compile(overtarget_rgx)
        # Otherwise, use the repl char straight
        else:
            ot_rgx = re.compile(repl)

        ### iterate through files ###
        # 'changed' tallies number of files actually worked on
        changed = 0
        for i in range(len(names)):
            # Save current target name for readability
            tgtname = names[i]
            # Construct full filename of original file (prob better to utilize SQL to get?)
            origfile = tgtname+'.'+exts[i]
            # Check for target char in current filename.  If there is, perform the sub & save the name
            if reg_rgx.search(tgtname) != None:
                build = re.sub(reg_rgx,repl,tgtname)
            ### Check for "more than expected" in a row of the replace string. 'None' skips the file in question. If there is, replace that with the original 'repl' string ###
                if ot_rgx.search(build) != None:
                    output[origfile] = re.sub(ot_rgx,repl,build)+'.'+exts[i]
                    changed +=1
                # Otherwise, just use the constructed name
                else:
                    output[origfile] = build+'.'+exts[i]    
                    changed +=1
        print("Total files changed: ",changed)  # ux
        return output, target, repl


    def __sqlq__(self,query,inp=None):
        '''This method helps us gather info related to the targeted files from the db, so we can perform subsequent functions accurately'''
        out = []
        #### Input check & parsing to orig (list of originals) and tgts (list of target changes)
        if type(inp) == tuple:
            orig = list(inp[0].keys())
            tgts = list(inp[0].values())
        elif type(inp) == dict:
            orig = list(inp.keys()) 
            tgts = list(inp.values())
        else:
            raise TypeError("Input is not a dict or tuple")
        ### Special query - appends WHERE clause to input QUERY (which should only be SELECT-FROM), which narrows selection to the rows matching the targets.
        for i in range(len(orig)):
            q = query + " WHERE filename='{}'".format(orig[i])
            self.crs.execute(q)
            qout = self.crs.fetchall()
            out.append((qout[0][0],qout[0][1],tgts[i]))
        return out    
                

    def __renamer__(self,inp,cpath=None):
        # Accounting for tuple input from changeChar. 
        if type(inp) == tuple:
            inp = inp[0]
        tgt_set = self.__sqlq__("SELECT path, filename FROM catalogue",inp)
        ### W/O CPATH, in-place
        if cpath == None:
            for s in range(len(tgt_set)):
                path = tgt_set[s][0]+'/'
                orig = path+tgt_set[s][1]
                new = path+tgt_set[s][2]
                os.rename(orig,new)
        ### IF CPATH GIVEN...###
        else:
            import shutil as sh
            # check for path has '/', and if not, build complete path for it
            if '/' not in cpath:
                cpath = os.getcwd()+'/'+cpath
            # Chk for cpath exists, make if not
            if os.path.exists(cpath) != True:
                os.mkdir(cpath)
                print("Directory created: ",cpath)
            else: print("Directory pre-existing")
            ### Process targets ### 
            for s in range(len(tgt_set)):
                # Vars for readability
                path = tgt_set[s][0]+'/'
                orig = path+tgt_set[s][1]
                # attempt to copy files to cpath
                try:
                    sh.copy2(orig, cpath)
                except Exception as e:
                    print("copy error", e.__class__, '-',e)
                # Do the renaming
                copied = cpath +'/'+ tgt_set[s][1]
                new = cpath+'/'+tgt_set[s][2]
                os.rename(copied,new)

                
    def fileRename(self,method='case',cpath=None,tcase=None,tgt=None,repl=None):
        # Populate db with file info
        self.__collectFile__(self.tpath)
        # Check value of 'method' arg, exception if missing or wrong
        if method == 'case':
            # Accounting for 'cpath' arg, then doing the actual renaming
            if cpath != None:
                print(self.__renamer__(self.__changeCase__(tcase),cpath))
            elif cpath == None:
                print(self.__renamer__(self.__changeCase__(tcase)))
            else:
                raise Exception("Unresolved issue with custom path") # Seems to be unnecessary
        elif method == 'char':
            # Accounting for 'cpath' arg then doing the actual renaming
            if cpath != None:
                print(self.__renamer__(self.__changeChar__(repl,tgt),cpath))
            elif cpath == None:
                print(self.__renamer__(self.__changeChar__(repl,tgt)))
            else:
                raise Exception("Unresolved issue with custom path")
        else:
            raise TypeError("method arg must be either case|char")
