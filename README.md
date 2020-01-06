# nhk-pronunciation
NOTE: This addon is no longer supported because a much better addon has been released for Anki, which you can download [here](https://ankiweb.net/shared/info/278530045) (only supports Anki 2.1). The new addon took inspiration from this addon (including apparently some source code at first but I don't think it has any of it now), and I spoke with the developer some throughought its creation in order to vet it. I highly recommend using that instead.

Anki2 Add-On to look-up the pronunciation of Japanese expressions. THIS VERSION ONLY WORKS WITH ANKI 2.0.

Always back up your decks and test on a couple cards before bulk adding. KNOWN BUGS (will delete this message when it's fixed): 1:  conjugated words in sentences, and words that can be interpreted in multiple ways (e.g. 確かめる can be viewed by the program as 確か+める) may cause junk text to be written to your destination field. 2: Spaces before words with hurigana are removed even when color hasn't been added. 3: Parentheses in your color field can cause a memory error.

2.0 version updated to add support for:
 - parsing fields containing multiple/conjugated words, 
whether they are inside sentences/fragments or separated by punctuation/symbols, etc. 
 - optional expression field auto-correction to 原形 (citation/dictionary form); 
 - accent-dependent colorization to automate [this process](https://www.youtube.com/watch?v=cy7GvwI7uV8&t=4m10s)(note that the default colors are different from the video; see below for how to customize them);
 - automatically adding audio files to your cards
 - bug fixes

See commits for full details.

LATEST UPDATES:
 - New correct_expressions option, which replaces your expression with 原形(s) according to Mecab's results. Not recommended if your expression is a sentence. Recommended only if your workflow requires the citation form of words.
  - All available sound files are added to words, so you now get to hear all accents. Also fixes the problem of accidentally getting a sound file for the wrong reading of a word.
  - config files is now separate from the main file, allowing you to easily update the main file without changing the config file (unless config variables are changed in the future :P )

Features that may be added in future releases include a new menu option to color all nontrivial words in a field based on accent (you can already do this; see below), the ability to simultaneously color multiple fields based on the same source expressions's accent, and an option to color words inside sentences even when they are conjugated (currently, to prevent confusion of accents, depending on your settings words are either changed to their citation form before coloring, or are not colored unless they are in citation form).

Installation:
1. Make sure you have the [Japanese Support Addon](https://ankiweb.net/shared/info/3918629684) installed already.
2. Make sure you have the [NHK accent plugin](https://ankiweb.net/shared/info/932119536) installed already.
3. Open your Anki addons folder by going to Tools -> Add-ons - Open Add-ons Folder in Anki.
4. Copy the files nhk_pronunciation.py and nhk_pronunciation_config.json into your addons folder, overwriting the old nhk_pronunciation.py file and (possibly) the old nhk_pronunciation_config.json file.
5. You need to copy the bs4 folder too if you don't have one. This dependency may by removed in the future, but for now you need it.
6. Open your Anki addons folder again as in step 3 and open nhk_pronunciation_config.json in a text editor, and then edit and set the variables below to your liking (don't forget to save).

Usage:
So that users don't have to redo their settings every time the addon is updated (the frequency of which will hopefully decrease soon), and because the number of settings has been growing, configuration can now be found in the nhk_pronunciation_config.json file. Additional comments on configuration can still be found at the top of the nhk_pronunciation.py file. When you adjust the settings in the config file, boolean values must be lowercase, you must have commas between different variables, and strings must be surrounded by double quotes ("").

Modify the following variables in the file to get different functionalities. Functionality was designed to be intuitive, but back up your files (and don't forget about the undo buttons) before adding in bulk. You can undo a bulk addition, but to be safe I recommend trying out different options with a single card at first. If you are confused, example default values can be found in the nhk_pronunciation.py file.

One possible setup users like is to set 

srcFields = ["Expression"]

colorFields = ["Reading"] 

color_sentence = true 

extend_expressions = true 

readings = true 

regenerate_prons = false

And the rest of the variables to your liking. (Recommended workflow: First bulk add Japanese support readings, and then bulk add pronunciation). You must set readings = false if the field you're adding color to doesn't include readings.

This plugin adds sound/color based on the first pronunciation, so if that is incorrect you will need to fix it manually when the card comes up - so pay attention during your initial reviews. You can use goldendict to get the correct sound file quickly (right click on the speaker icon in the NHK dictionary, and click save sound; then drag and drop the saved file in the sound field in your card).

How to add pronunciation for all words in a sentence: Set srcFields = ['Sentence'] (i.e. to a field that contains a sentence you want to color), and colorFields = ['Reading'] or colorFields = ['Sentence'] depending on what you want to color. Note that the Pronunciation field will be filled out with pronunciations for all words, so you'll need another field that specifies the focus word in order to remind yourself of what it is. 

srcFields = ["name of the field you want to write the accent to dstFields of"]    

dstFields = ["name of the field where you want accent info from srcFields to go"]

sndFields = ["if you have an empty audio field and have audio files labeled with words, put the folder name here"]

add_sound = true #set to true if you want to add audio to your cards

If you have the NHK audio files from Yogapants, you can have those automatically added to your Anki media collection and put in an empty audio field in your cards. Note that some mobile devices or SD cards won't handle .wav files properly, so if you are concerned, before runnning the addon, you can convert your audio files to .mp3 using [ffmpeg](http://ffmpeg.org/ffmpeg.html#Video-and-Audio-file-format-conversion). You need to specify the soundFolder variable (below) if you want to use these files. You should leave sndFields blank if you don't want the addon to try to automatically add sound files.

colorFields = ["name of the field you want to add color to based on the contents of srcFields"]

If you don't want to automatically have color added to words, set colorFields = [] or colorFields = [""]. This will only use the color/accent information of what's found in srcFields.

color_sentence = true #default

Set color_sentence = true if colorFields (above) often contains a sentence...otherwise set to false (sentences will usually be automatically detected). Specifically, set to true if you want colorFields to not be overwritten, but merely to be colorized to the extent possible without changing its contents. Normally a word in a sentence will only be colorized if it is in citation form. This is to prevent confusion about the accent. The accent color here always indicates the accent of the dictionary/citation form of the word. There is currently no support for simultaneously coloring the an expression field and a sentence field. I'm working on adding that, but let me know if you want that or I might not bother. If color_sentence = false and the colorField is automatically determined not to be part of a sentence, if extend_expressions = true it will be changed into citation form and colored fully.

readings = false

Set readings to true if you use brackets to indicate readings; otherwise brackets that break up words will cause those words to not be colored. The Reading field must already be populated with text that contains readings inside brackets in order for this to work.


unaccented_color = "green"

head_color = "red"

tail_color = "orange"

mid_color = "blue"

Change the above variables to affect the colors assigned to 平板型、頭高型、尾高型、and 中高型、respectively.


extend_expressions = false # Replace expression with citation forms of relevant terms as appropriate (Default: false)

Further down you'll find these variables:

soundFolder = u'path to the NHK sound files if you have them'

media_folder = media_folder = os.pardir + os.sep + os.pardir + os.sep + "User 1" + os.sep + "collection.media"

This is your Anki media collection. You probably don't need to change the media_folder value, but if you do, just put the path here in quotes (e.g. "../../User 1/collection.media").

#delimiter to use between each word in a corrected expression (Default: '・')
modification_delimiter = '・' # only used if extend_expressions is true

regenerate_prons = true # Regenerate pronunciations even if they already exist?
