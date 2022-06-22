'''Simple Test File for bulkrenamer
*****************
Just a few disorganized tests
'''

import bulkrenamer as b

#search = b.Catalogue()
search = b.Catalogue('../mediaconverter/tests/media')
#search.fileRename(method='char',cpath='out2',tgt=' ', repl='$')
search.fileRename(method='case',cpath='out2',tcase='upper')