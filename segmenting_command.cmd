ffmpeg -y -i %1 -c:a aac -b:a 128k -muxdelay 0 -f segment -sc_threshold 0 -segment_time %4 -segment_list %2 -segment_format mpegts %3
: %1 = input file
: %2 = name of m3u8 manifest file
: %3 = output segment filename format, for example 'segment%d.m4a'
: %4 = segment length in time