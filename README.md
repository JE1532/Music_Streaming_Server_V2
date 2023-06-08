TODO:
1. fix scrollbar bugs - half done - buglog?
2. fix stream processor bugs - half done - buglog?
3. add support for the multiple wav formats or change player and processor for playing via mplayer
4. add CAPTCHAs
5. add upload mechanism for profile pictures
6. release unused picture files
7. look at bugs that occur when song (play) buttons (records with images) are pressed many times in a short span of time.


BUG-LOG:
1. I think transition from first to second segment while playing LongSoundExample.wav is not smooth. Maybe happens for other segments too.
    I have investigated this more significantly - problem seems to have something to do with convertion to wav (from m4a format)
    since it was recreated manually by convertions. May have something to do with poor mpeg-4 support by ffmpeg in windows.
2. client opens new file for every picture used without releasing filenames
3. when the same playbutton is clicked multiple times quickly, the client raises an error