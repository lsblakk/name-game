import os
import fetch
import json
import datetime

LOAD_PEOPLE = os.path.join(fetch.STATIC_FILES_DIR, 'load-people.js')
MANIFEST = os.path.join(fetch.STATIC_FILES_DIR, 'cache.manifest')
NO_PHOTO = os.path.join(fetch.STATIC_FILES_DIR, 'images', 'no-photo.jpg')

def main():
    print 'Writing %s.' % LOAD_PEOPLE

    people = json.load(open(fetch.JSON_FEED_FILENAME, 'r'))
    nophoto = open(NO_PHOTO, 'rb').read()

    def is_no_photo(filename):
        abspath = os.path.join(fetch.THUMBNAIL_DIR, filename)
        return open(abspath, 'rb').read() == nophoto

    thumbnails = [filename for filename in os.listdir(fetch.THUMBNAIL_DIR)
                  if not is_no_photo(filename)]

    people_list = []
    for email, info in people.items():
        info['name'] = info['name'].strip()
        info['email'] = email
        if '%s.jpg' % email in thumbnails:
            info['thumbnail'] = True
        people_list.append(info)
    
    def compare(a, b):
        return cmp(a['name'], b['name'])
    
    people_list.sort(compare)

    f = open(LOAD_PEOPLE, 'w')
    f.write('onLoadPeople(%s);' % json.dumps(people_list))
    f.close()

    print 'Writing %s.' % MANIFEST

    f = open(MANIFEST, 'w')
    f.write('CACHE MANIFEST\n')
    f.write('# Created %s\n' % str(datetime.datetime.now()))
    for dirpath, dirnames, filenames in os.walk(fetch.STATIC_FILES_DIR):
        filenames = [filename for filename in filenames
                     if filename not in ['cache.manifest']]
        relpath = dirpath[len(fetch.STATIC_FILES_DIR)+1:]
        if relpath:
            relpath += '/'
        for filename in filenames:
            f.write('%s%s\n' % (relpath, filename))
    f.close()

if __name__ == '__main__':
    main()
