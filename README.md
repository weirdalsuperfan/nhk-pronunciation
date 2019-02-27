# nhk-pronunciation
Anki2 Add-On to look-up the pronunciation of Japanese expressions.

2.0 version updated to add support for parsing fields containing multiple/conjugated words, 
whether they are inside sentences/fragments or separated by punctuation/symbols, etc. Also adds optional expression field auto-correction to 原形 (citation/dictionary form); accent-dependent colorization to automate [this process](https://www.youtube.com/watch?v=cy7GvwI7uV8&t=4m10s), automatically adding audio files to your cards; and bug fixes. See commits for full details.


Installation:
1. Make sure you have the [NHK accent plugin](https://ankiweb.net/shared/info/932119536) installed already.
2. Open your Anki addons folder by going to Tools -> Add-ons - Open Add-ons Folder in Anki.
3. Copy the file nhk_pronunciation.py into your addons folder, overwriting the old nhk_pronunciation.py file.
4. You need to copy the bs4 folder too if you don't have one. This dependency may by removed in the future, but for now you need it.

Usage:
Modify the following variables in the file to get different functionalities. Functionality was designed to be intuitive, but back up your files (and don't forget about the undo buttons) before adding in bulk. You can undo a bulk addition, but to be safe I recommend trying out different options with a single card at first. If you are confused, example default values can be found in the nhk_pronunciation.py file.

srcFields = ['name of the field you want to write the accent to dstFields of']    

dstFields = ['name of the field where you want accent info from srcFields to go']

sndFields = ['if you have an empty audio field and have audio files labeled with words, put the folder name here']

If you have the NHK audio files from Yogapants, you can have those automatically added to your Anki media collection and put in an empty audio field in your cards. Note that some mobile devices or SD cards won't handle .wav files properly, so if you are concerned, before runnning the addon, you can convert your audio files to .mp3 using [ffmpeg](http://ffmpeg.org/ffmpeg.html#Video-and-Audio-file-format-conversion). You need to specify the soundFolder variable (below) if you want to use these files. You should leave sndFields blank if you don't want the addon to try to automatically add sound files.

colorFields = ['name of the field you want to add color to']

If you don't want to automatically have color added to words, set colorFields = [] or colorFields = ['']

color_sentence = True #default

Set color_sentence = True if colorFields (above) often contains a sentence...otherwise set to False (sentences will usually be automatically detected). Specifically, set to True if you want colorFields to not be overwritten, but merely to be colorized to the extent possible without changing its contents. Normally a word in a sentence will only be colorized if it is in citation form. This is to prevent confusion about the accent. The accent color here always indicates the accent of the dictionary/citation form of the word.

unaccented_color = 'green'

head_color = 'red'

tail_color = 'orange'

mid_color = 'blue'

Change the above variables to affect the colors assigned to 平板型、頭高型、尾高型、and 中高型、respectively.

modify_expressions = False #if colorFields is empty, changes the srcField; otherwise changes the colorField

Replace expression and/or colorFields with citation forms of relevant terms as appropriate (Default: False)

Further down you'll find these variables:

soundFolder = u'path to the NHK sound files if you have them'

media_folder = "../../User 1/collection.media"

This is your Anki media collection. You probably don't need to change the media_folder value, but if you do, just put the path here.

