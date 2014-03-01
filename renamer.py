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

def cutTheFat(input):
    '''
    Culls the herd, cuts the fat, trims the lines.
    Removes all meta-properties from the filename.
    '''
    replace = ["720p", "1080p", "r5", "r6", "xvid", "ac3", "dd5.1", "5.1", "hq", "bluray", "x264", "480p", \
    "brrip", "web-dl", "h264", "h.264", "dvdrip", "hddvd", "aac2.0", "aac2", "dts", "hdrip", "avchd", "blu-ray"]
    
    f = ""
    
    #convert to lowercase
    for char in input:
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
    title = title.encode("utf-8")
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
        return movies[0]
    elif keystroke == "" and not movies:
        print 'Skipping.\n'
        return None
    #do we want to skip this movie?
    elif keystroke == "s":
        print 'Skipping.\n'
        return None
    else:
        try:
            #if keystroke is not null, then see if it's an index out of the movies list
            selection = movies[int(keystroke)]
            return selection
        except ValueError, IndexError:
            #guess not, so try searching the omdb for it
            return selectID(search(keystroke))

def move(location, f, imdb):
    '''
    Either create a folder for this movie and move it or
    append the couchpotato tag to the subfolder the movie is in
    '''
    #check if this is in the root folder
    if location == workingDir:
        #if it is, then create a folder and move the file
        new_folder = os.path.join( location, f + ".cp(" + imdb + ")" )
        try:
            os.mkdir( new_folder )
            os.rename( os.path.join(location, f), os.path.join( new_folder, f ))
            print "Moved file into folder\n"
        except OSError as e:
            print "Error: " + e
        
    else:
        #if not then append the .cp(tt##) tag to the subfolder
        try: 
            os.rename ( location, location + ".cp(" + imdb + ")" )
            print "Renamed folder\n"
        except OSError as e:
            print "Error: " + e

def run():
    ext = (".mkv", ".avi", ".divx", ".xvid", ".mov", "mp4")
    for (dirpath, dirnames, filenames) in os.walk(workingDir):
        #check to make sure this isn't already a sorted folder
        if ".cp(tt" not in dirpath:
            for f in filenames:
                #check if the file still exists
                if os.path.isfile(os.path.join(dirpath, f)):
                    #check to make sure it has the extension of a movie.
                    if os.path.splitext(f)[1].lower() in ext:
                        #clean it upsud
                        clean = cutTheFat(f)
                        print "New Title: ", clean, " -- ", os.path.split(dirpath)[1] + "/" + f
                        #find out what it is
                        result = selectID(search(clean))
                        if result:
                            #if it's anything, then move it!
                            move(dirpath, f, result['imdbID'])
                else:
                    print 'File already sorted. Skipping: %s\n' % f


if __name__ == '__main__':
    run()