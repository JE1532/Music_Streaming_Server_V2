TODO:
1. fix scrollbar bugs
2. fix stream processor bugs
3. fix vlc bug - server stops being able to stream after streaming to vlc once
4. add upload mechanism for profile pictures
5. release unused picture files
6. add upload mechanism for records (=songs and albums)
7. look at bugs that occur when song (play) buttons (records with images) are pressed many times in a short span of time.


BUG-LOG:
1. I think transition from first to second segment while playing LongSoundExample.wav is not smooth. Maybe happens for other segments too
2. streaming to vlc once leaves server unable to stream.
3. client opens new file for every picture used without releasing filenames
4. client seems to stop playing after finishing 1 track?