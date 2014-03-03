#!/usr/bin/python
#usage: renamer.py /directory/to/files
'''
Get all files and subfolders.
Strip all the random shit from the filenames.
Queries the OMDB to see if we can figure out what movie it is.
User selects from list or accepts default
or skips movie or inputs another search string for the movie.
Then creates a folder with the appropriate tagging for CouchPotato and 
moves the file into it. If the file is already in a subfolder, then
just append the cp(ttIMDB) tag to it.
'''
import json, urlparse, sys, os
# from os import walk, path, mkdir, join
from subprocess import call
from urllib import quote
from urllib2 import urlopen
from re import sub


#All them globals, son.
#or just the one.
workingDir = sys.argv[1]

def cutTheFat(filename):
    '''
    Culls the herd, cuts the fat, trims the lines.
    Removes all meta-properties from the filename.
    '''
    f = ""
    
    cap_replace = ["LIMITED", "EXTENDED", "UNRATED"]

    for rep in cap_replace:
        filename = filename.replace(rep, "")

    replace = ["720p", "1080p", "r5", "r6", "xvid", "ac3", "dd5.1", "5.1", "hq", "bluray", "x264", "480p", \
    "brrip", "web-dl", "h264", "h.264", "dvdrip", "hddvd", "aac2.0", "aac2", "dts", "hdrip", "avchd", "blu-ray", \
    "hdtv", "webrip"]
    
    
    #convert to lowercase
    for char in filename:
        f += char.lower()
    #strip the f extension    
    f = os.path.splitext(f)[0]
    #remove all the junk
    for rep in replace:
        f = f.replace(rep, "")
    #strip anything after, and including the last dash i.e. "-FlaWlESS" the group name
    try:
        f = f[0 : len(f) - 1 - f[::-1].index("-")]
    except ValueError:
        pass
    #now replace all dots, dashes with spaces
    f = f.replace(".", " ").replace("-", " ").replace("_", " ")
    #and then remove the year
    f = sub(r'19[\d]{2}|20[\d]{2}', '', f)
    #finally strip down and return yo'self
    return f.strip()

def search(title):
    '''
    Searches the OMDB for the specified string
    and returns the result, if any.
    '''
    try: 
        title = title.encode("utf-8")
    except UnicodeDecodeError:
        print "Error processing non-unicode text."
        return None
    url = "http://www.omdbapi.com/?r=json&s=%s" % quote(title)
    #print url
    data = urlopen(url).read().decode("utf-8")
    data = json.loads(data)
    if data.get("Response") == "False":
        return None
    return data.get("Search", [])

def selectID(movies):
    '''
    Queries the user to decide which result is best,
    or allows the user to enter a new search string for this movie,
    or to skip the movie altogether.
    '''
    if movies and len(movies) > 1:
        print "It looks like there are several possibilities for this movie."
    print "enter to accept, (#) to select, (s) to skip"
    print "Or type a new search query for this movie."
    index = 0
    if movies:
        for movie in movies:
            print "%s[%s] %s (%s)" % ("*" if index == 0 else "", index, movie['Title'], movie['Year'])
            index+=1
    else:
        print "*[] Skip"
    keystroke = raw_input("selection: ")
    #if it's a blank keystroke, then just continue with the default
    if keystroke == "" and movies:
        print '\n'
        return movies[0]
    elif keystroke == "" and not movies:
        print 'Skipping.\n'
        return None
    #do we want to skip this movie?
    elif keystroke == "s":
        print 'Skipping.\n'
        return None
    else:
        print '\n'
        try:
            #if keystroke is not null, then see if it's an index out of the movies list
            selection = movies[int(keystroke)]
            return selection
        except ValueError, IndexError:
            #guess not, so try searching the omdb for it
            return selectID(search(keystroke))


def move(location, f):
    '''
    Create a folder for this movie and move it if it
    is not already in a subfolder.
    '''
    #check if this is in the root folder
    if location == workingDir:
        #if it is, then create a folder and move the file
        new_folder = os.path.join( location, os.path.splitext(f)[0] )
        try:
            os.mkdir( new_folder )
        except OSError:
            pass
        try:
            os.rename( os.path.join(location, f), os.path.join( new_folder, f ))
            print "Moved file into folder\n"
            return new_folder
        except OSError as e:
            print "Error: " + e.strerror
    else:
        return location

def createNFO(directory, id):
    '''
    Create an NFO with the imdb link for this movie.
    '''
    with open(os.path.join(directory, 'couchpotato.nfo'), 'a') as nfo:
        nfo.write('http://www.imdb.com/title/%s' % id)
        
def chooseBetween(folder, filename):
    fo = folder.rstrip('\\').rstrip('//')
    fi = os.path.splitext(filename)[0]
    if len(fo) >= len(fi):
        return os.path.basename(folder)
    return filename

def nFOExists(files):
    for f in files:
        if "nfo" in toLowerCase(f):
            return True
    return False

def toLowerCase(input):
    out = ""
    for char in input:
        out += char.lower()
    return out
        
def run():
    ext = (".mkv", ".avi", ".divx", ".xvid", ".mov", "mp4")
    for (dirpath, dirnames, filenames) in os.walk(workingDir):
        #check to make sure this isn't already a sorted folder
        if ".cp(tt" not in dirpath and not nFOExists(filenames):
            for f in filenames:
                #check if the file still exists
                if os.path.isfile(os.path.join(dirpath, f)):
                    #check to make sure it has the extension of a movie.
                    if os.path.splitext(f)[1].lower() in ext:
                        #Choose between the directory name or the filename then clean the string up
                        clean = cutTheFat(chooseBetween(dirpath, f))
                        print "New Title: ", clean, " -- ", os.path.split(dirpath)[1] + "/" + f
                        #find out what it is
                        result = selectID(search(clean))
                        if result:
                            #check if it needs it's own folder and move it
                            movedTo = move(dirpath, f)
                            createNFO(movedTo, result['imdbID'])
                else:
                    print 'File already sorted. Skipping: %s\n' % f


if __name__ == '__main__':
    run()
