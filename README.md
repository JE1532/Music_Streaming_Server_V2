TODO:
1. add TLS
2. encrypt all approaches to database with base64 to prevent SQL injection.
3. fix scrollbar bugs
4. fix vlc bug - server stops being able to stream after streaming to vlc once
5. add upload mechanism for profile pictures
6. release unused picture files
7. add upload mechanism for records (=songs and albums)


BUG-LOG:
1. moving scrollbar when pause causes scrollbar and song player to de-sync.
2. songs are played from second segment sometimes.
3. streaming to vlc once leaves server unable to stream.
4. client opens new file for every picture used without releasing filenames