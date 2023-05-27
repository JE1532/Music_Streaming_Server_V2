TODO:
1. fix scrollbar bugs - half done - buglog?
2. fix stream processor bugs - half done - buglog?
3. add next and prev mechanism for playlists
4. add internal and external name separation
5. add support for the multiple wav formats or change player and processor for playing via mplayer
6. add CAPTCHAs
7. add upload mechanism for profile pictures
8. release unused picture files
9. add upload mechanism for records (=songs and albums)
10. look at bugs that occur when song (play) buttons (records with images) are pressed many times in a short span of time.


BUG-LOG:
1. I think transition from first to second segment while playing LongSoundExample.wav is not smooth. Maybe happens for other segments too.
2. client opens new file for every picture used without releasing filenames
3. when the same playbutton is clicked multiple times quickly, the client raises an error
4. when two different playbuttons are pressed quickly, the client doesn't transition properly