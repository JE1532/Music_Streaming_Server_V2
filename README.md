TODO:
1. fix scrollbar bugs
2. fix stream processor bugs
3. fix vlc bug - server stops being able to stream after streaming to vlc once
4. add upload mechanism for profile pictures
5. release unused picture files
6. add upload mechanism for records (=songs and albums)
7. look at bugs that occur when song (play) buttons (records with images) are pressed many times in a short span of time.


BUG-LOG:
1. moving scrollbar when pause causes scrollbar and song player to de-sync.
2. songs are played from second segment sometimes.
3. streaming to vlc once leaves server unable to stream.
4. client opens new file for every picture used without releasing filenames