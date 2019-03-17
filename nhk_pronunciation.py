# -*- coding: utf-8 -*-

from collections import namedtuple, OrderedDict
import re
import codecs
import os
import io
import json
from os import listdir
from os.path import isfile, join, isdir
import cPickle
import time
from string import punctuation
from bs4 import BeautifulSoup
from shutil import copy


from aqt import mw
from aqt.qt import *
from aqt.utils import showText

import japanese
from japanese.reading import MecabController as jsupport_mecab

import sys, platform, subprocess, aqt.utils
from anki.utils import stripHTML, isWin, isMac


# ************************************************
#                User Options                    *
# ************************************************

dir_path = os.path.dirname(os.path.normpath(__file__))
if sys.version_info.major == 2:
    import json
    config = json.load(io.open(os.path.join(dir_path, 'nhk_pronunciation_config.json'), 'r'))
else:
    raise Exception("This version only supports Anki 2.0; please use the 2.1 version: https://ankiweb.net/shared/info/932119536")
"""
EDIT SETTINGS IN nhk_pronunciation_config.json
THIS COMMENT IS ONLY HERE FOR EXPLANATION


# Style mappings (edit this if you want different colors etc.):
config["styles"] = {'class="overline"': 'style="text-decoration:overline;"',
          'class="nopron"':   'style="color: royalblue;"',
          'class="nasal"':    'style="color: red;"',
          '&#42780;': '&#42780;'}

# Expression, Reading and Pronunciation fields (edit if the names of your fields are different)
config["srcFields"] = ['Expression']    
config["dstFields"] = ['Pronunciation']
config["sndFields"] = ['Audio']
config["colorFields"] = ['Expression']
config["is_sentence"] = False #set to True if your Expression is a sentence
config["color_sentence"] = False #set to True if config["colorFields"] often contains a sentence...otherwise don't
#set config["readings"] to True if you use brackets to indicate config["readings"]; 
#otherwise brackets that break up words will cause those words to not be colored
config["readings"] = False #if True, will preserve config["readings"] to the colored field. TURN OFF IF NOT COLORING A config["readings"] FIELD
config["unaccented_color"] = 'green'
config["head_color"] = 'red'
config["tail_color"] = 'orange'
config["mid_color"] = 'blue'

# Extend expression with citation forms of relevant terms as appropriate (Default: False)
config["extend_expressions"] = True
# Replace expression with 原形 according to Mecab (overrides config["extend_expressions"])
# Use only if you trust Mecab to not split words too much, or if you really need the 原形
config["correct_expressions"] = True

#delimiter to use between each word in a corrected expression (Default: '・')
config["modification_delimiter"] = '・' # only used if config["extend_expressions"] is True

# Regenerate pronunciations even if they already exist?
config["regenerate_prons"] = True

global config["add_sound"]
config["add_sound"] = True #set to true if you want to add audio to your cards

# Use hiragana instead of katakana for config["readings"]?
config["pronunciation_hiragana"] = False
"""
# ************************************************
#                Global Variables                *
# ************************************************

# Paths to the database files and this particular file
thisfile = os.path.join(mw.pm.addonFolder(), "nhk_pronunciation.py")
derivative_database = os.path.join(mw.pm.addonFolder(), "nhk_pronunciation.csv")
derivative_pickle = os.path.join(mw.pm.addonFolder(), "nhk_pronunciation.pickle")
accent_database = os.path.join(mw.pm.addonFolder(), "ACCDB_unicode.csv")
soundFolder = u'D:/Dropbox (Personal)/Japan/Pronunciation/NHKOjadAccentsJson/NHKAccentMedia/audio'
soundDict = {}
soundFiles = []
media_folder = os.pardir + os.sep + os.pardir + os.sep + "User 1" + os.sep + "collection.media"
if config["add_sound"] and isdir(soundFolder):
    soundFiles = [f for f in listdir(soundFolder)]# if isfile(join(soundFolder, f))]
    for sound in soundFiles:
        if '.yomi' in sound:
            soundDict[sound.split('.')[0]] = sound
    #soundDict = {sound.split('.')[0]: sound for sound in soundFiles if '.yomi' in sound}
    
# "Class" declaration
AccentEntry = namedtuple('AccentEntry', ['NID','ID','WAVname','K_FLD','ACT','midashigo','nhk','kanjiexpr','NHKexpr','numberchars','nopronouncepos','nasalsoundpos','majiri','kaisi','KWAV','midashigo1','akusentosuu','bunshou','ac'])

# The main dict used to store all entries
thedict = {}

hiragana = u'がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ' \
               u'あいうえおかきくけこさしすせそたちつてと' \
               u'なにぬねのはひふへほまみむめもやゆよらりるれろ' \
               u'わをんぁぃぅぇぉゃゅょっ'
katakana = u'ガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ' \
               u'アイウエオカキクケコサシスセソタチツテト' \
               u'ナニヌネノハヒフヘホマミムメモヤユヨラリルレロ' \
               u'ワヲンァィゥェォャュョッ'

numerals = u"一二三四五六七八九十０１２３４５６７８９"
               
#conjugation elements and other elements to not worry about
conj = ['お','ご','御','て','いる','ない','た','ば','ます','ん',
'です','だ','たり','える','うる','ある','そう','がる','たい','する','じゃ','う',
'させる','られる','せる','れる','ぬ']

particles_etc = ['は','が','も','し','を','に','と','さ','へ','まで','もう','まだ', 'で',
'ながら','より','よう','みたい','らしい','こと','の','もの','みる','わけ','よ','ね','か','わ','ぞ','ぜ']

j_symb = '・、※【】「」〒◎×〃゜『』《》〜〽。〄〇〈〉〓〔〕〖〗〘 〙〚〛〝 〞〟〠〡〢〣〥〦〧〨〫  〬  〭  〮〯〶〷〸〹〺〻〼〾〿'

#Ref: https://stackoverflow.com/questions/15033196/using-javascript-to-check-whether-a-string-contains-japanese-characters-includi/15034560#15034560               
regex = ur'[^\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\uff66-\uff9f\u4e00-\u9fff\u3400-\u4dbf]+'#+ (?=[A-Za-z ]+–)'
jp_regex = re.compile(regex, re.U)

# ************************************************
#                  Japanese Support              *
# ************************************************

mecabArgs = ['--node-format=%f[6] ', '--eos-format=\n',
            '--unk-format=%m[] ']

def escapeText(text):
    # strip characters that trip up kakasi/mecab
    text = text.replace("\n", " ")
    text = text.replace(u'\uff5e', "~")
    text = re.sub("<br( /)?>", "---newline---", text)
    text = stripHTML(text)
    text = text.replace("---newline---", "<br>")
    return text

if sys.platform == "win32":
    si = subprocess.STARTUPINFO()
    try:
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    except:
        si.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
else:
    si = None

# Mecab
##########################################################################

def mungeForPlatform(popen):
    if isWin:
        popen = [os.path.normpath(x) for x in popen]
        popen[0] += ".exe"
    elif not isMac:
        popen[0] += ".lin"
    return popen


class MecabController(object):

    def __init__(self):
        self.mecab = None

    def setup(self):
        base = "../../addons/japanese/support/"
        self.mecabCmd = mungeForPlatform(
            [base + "mecab"] + mecabArgs + [
                '-d', base, '-r', base + "mecabrc"])
        os.environ['DYLD_LIBRARY_PATH'] = base
        os.environ['LD_LIBRARY_PATH'] = base
        if not isWin:
            os.chmod(self.mecabCmd[0], 0o755)

    def ensureOpen(self):
        if not self.mecab:
            self.setup()
            try:
                self.mecab = subprocess.Popen(
                    self.mecabCmd, bufsize=-1, stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    startupinfo=si)
            except OSError as e:
                raise Exception(str(e) + ": Please ensure your Linux system has 64 bit binary support.")
    
    def reading(self, expr):
        self.ensureOpen()
        expr = escapeText(expr)
        self.mecab.stdin.write(expr.encode("euc-jp", "ignore") + b'\n')
        self.mecab.stdin.flush()
        expr = self.mecab.stdout.readline().rstrip(b'\r\n').decode('euc-jp')
        return expr


# ************************************************
#                  Helper functions              *
# ************************************************
def test_cases():
    """
    List of things tested with via anki
    
    A 頭高型 word with 小さい文字 in the first mora 重要
    A word that normally starts with お・御 おみおつけ (御御御付けなどは not in the dictionary)
    something with 々 and kana after it 着々と
    easy sentence 庭には二羽鶏がいる
    sentence with words that can't be looked up
    all kana sentence　あのかわいいものがいいですね
    single word (all kana) からい
    single word (all kanji)　勉強
    single word (kana at beginning)　お茶
    single word (kana or particle at end)　明らかな
    single word (kana in middle)　世の中
    single word (conjugated)　気に入った
    single word (citation form) 面白い
    word made up of useless things したがりませんか？
    2 words separated by ・　お支払い・前払い
    3 words, all conjugated, with HTML formatting, at least 
        one of which (the first) isn't in the accent dict in any form
    4 words, all lookup-able (but conjugated), no formatting, each with a 0-3 accent
    a compound word that mecab splits but that is actually in the dictionary 研究者
    """
    pass
    
"""
def new_mecab(mecabArgs_new):
    #command line testing function
    def munge(popen):
        popen = [os.path.normpath(x) for x in popen]
        popen[0] += ".exe"
        return popen
    mecabCmd_new = munge(
        [base + "mecab"] + mecabArgs_new + [
        '-d', base, '-r', base + "mecabrc"])
    mecab_new = subprocess.Popen(
                    mecabCmd_new, bufsize=-1, stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    startupinfo=si)
    def reading_new(expr):
        mecab_new.stdin.write(expr.encode("euc-jp", "ignore") + b'\n')
        mecab_new.stdin.flush()
        expr = mecab_new.stdout.readline().rstrip(b'\r\n').decode('euc-jp')
        print(expr)
        return expr
    return reading_new

"""
    
def katakana_to_hiragana(to_translate):
    katakana = [ord(char) for char in katakana]
    translate_table = dict(zip(katakana, hiragana))
    return to_translate.translate(translate_table)
      
      
def nix_punctuation(text):
    return ''.join(char for char in text if char not in punctuation)

    
def multi_lookup_helper(srcTxt_all, lookup_func):
    """
    Gets the pronunciation (or another type of dictionary lookup)
    for both the raw text and it without okurigana
    
    param list of strings srcTxt_all terms to look up with lookup_func
    param function lookup_func dictionary lookup function to send elements of srcTxt_all to
    """
    prons = []
    sounds = [] #search for all but just choose the first in the end
    #return True if all succeeded; good for skipping mecab (avoiding possibly oversplitting)
    all_hit = False
    count = 0
    colorized_words = [] #only appended to if the words are colored
    def replace_dup(text):
        char_dex = 1
        for char in text:
            if char_dex == len(text): break
            if char == text[char_dex]: text = text[:char_dex] + '々' + text[char_dex+1:]
            char_dex += 1
        return text
    def prons_n_colors(src):
        """real lookup function"""
        new_prons = lookup_func(src)
        if not new_prons: new_prons = lookup_func(replace_dup(src))
        if new_prons:
            #choose only the first prons when assigning color to the word
            src_for_colorization = original_reader.reading(src) if config["readings"] else src
            if isinstance(new_prons,list): colorized_words.append(add_color(src_for_colorization, new_prons[0]))
            #It can be either a list or a string, I guess
            prons.extend(new_prons) if isinstance(new_prons,list) else prons.append(new_prons)
            #prons.extend(new_prons)#I guess this separates the string into characters if it's 1 string
            
            try:
                if soundFiles:
                    for sound in soundFiles:
                        if '.yomi' in sound:
                            #raise Exception(sound.split('.')[0])
                            if sound.split('.')[0] == src:
                                sounds.append(sound)
            except Warning:
                raise Exception(sound.split('.')[0])
            return True
        #else just add the blank word, so you don't lose words
        colorized_words.append(src)
        return False
    
    if srcTxt_all:
        for srcTxt in srcTxt_all:
            if prons_n_colors(srcTxt): 
                count += 1
                continue
    
    if srcTxt_all and count == len(srcTxt_all): all_hit = True

    return colorized_words, sounds, prons, all_hit


def japanese_splitter(src):
    """Helper function for multi_lookup(src, lookup_func)
    but is its own function for modularity
    
    If multiple words are separated by a ・ (Japanese slash)
    or other punctuation, splits into separate words."""
    srcTxt_all = []
    src = soup_maker(src)
    #Separate the src field into individual words
    separated = re.sub(jp_regex, ' ', src)
    separated2 = nix_punctuation(separated)
    srcTxt_all = separated2.replace('・', ' ').split(' ')
    
    return srcTxt_all


def soup_maker(text):
    """para string text some text possibly formatted with HTML
    returns string src , the plaintext parsed from Beautiful soup"""
    soup = BeautifulSoup(text, "html.parser")
    src = soup.get_text()
    return src
    

def add_color(word, pron):
    """return HTML-encoded string c_word consisting of the given string word, + color"""
    non_mora_zi = ur'[ぁぃぅぉゃゅょァィゥェォャュョ]'
    raw_pron = soup_maker(pron)
    if "ꜜ" in raw_pron:
        #then it has an accent (i.e. a downstep symbol)
        if len(re.sub(non_mora_zi, r'',raw_pron).split("ꜜ")[0]) == 1:
            #then it's 頭高型 or single-mora
            c_word = '<font color="' + config["head_color"] + '">' + word + '</font>'
        elif len(raw_pron) != len(raw_pron.rstrip("ꜜ")):
            #then it's 尾高　[tail]
            c_word = '<font color="' + config["tail_color"] + '">' + word + '</font>'
        else:
            #then it's 中高　[middle]
            c_word = '<font color="' + config["mid_color"] + '">' + word + '</font>'
    else:
        #it's unaccented (平板)
        c_word = '<font color="' + config["unaccented_color"] + '">' + word + '</font>'
    
    return c_word


def reading_parser(raw_reading):
    """takes a string (possibly with multiple words)
    consisting of a mecab parse (separated by spaces) and returns just the base word
    Uses heuristics to eliminate conjugations and other excessive stuff mecab returns"""
    base = [x for x in raw_reading.split(" ") if x and 
    x not in conj and x not in particles_etc and 
    x not in j_symb and x not in punctuation and x not in numerals]
    only_japanese = [re.sub(jp_regex, '', a) for a in base]
    
    return only_japanese
    
    
def multi_lookup(src, lookup_func, colorTxt = None, separator = "  ***  "):
    """Has 3 functions: 1) If multiple words are separated by a ・ (Japanese slash)
    or other punctuation, gets the pronunciation for each word. 
    2) Parses words with Mecab if a simple split doesn't work
    3) adds color to the original expression and/or replaces it with citation forms"""
    #do_colorize = False

    #config["is_sentence"] = False # set to True if probably a sentence, to avoid modifying it
    #if config["colorFields"]:
    #    if not config["extend_expressions"]:
    #        raise Exception("Please set config["extend_expressions"] to True for auto-colorize to work")
    #    else: do_colorize = True

    prons, colorized_words, srcTxt_all = [], [], []
    src = re.sub(r"\s?([^[\]]*)\[[^[\]]*\]", r"\1", src) #for removing brackets that hurigana config["readings"] insert
    srcTxt_all = japanese_splitter(src)

    #__, _, prons, all_hit = multi_lookup_helper(srcTxt_all, lookup_func)
    
    #iterate through and replace 々 with the kanji preceding it
    new_src = src
    char_dex = 1
    for char in src:
        if char_dex == len(src): break
        if src[char_dex] == '々': new_src = src[:char_dex] + char + src[char_dex+1:]
        char_dex += 1

    #parse with mecab and add new terms to the entries to look up
    srcTxt_2 = reading_parser(reader.reading(soup_maker(new_src)))
    if config["correct_expressions"]:
        srcTxt_all = srcTxt_2
    else:
        srcTxt_all.extend([term for term in srcTxt_2 if term not in srcTxt_all])
    
    colorized_words, sounds, prons, all_hit = multi_lookup_helper(srcTxt_all, lookup_func)
    
    #if you couldn't split the words perfectly with a simple split, use mecab
    #or just use it anyway
    #if not all_hit: config["is_sentence"] = True
    if len(srcTxt_all) == 1 and not prons: config["is_sentence"] = True
    
    #TODO: improve sentence detection...by default assume it's not sentence?
    #case 1: original text is a conjugated word; mecab returns that + base form
    #case 2: original text is in base form; mecab returns that and len = 1
    #case 3: there are multiple conjugated separated by delimiters...mecab
    #results yield original + base * 2. 
    #case 4: there are multiple phrases separated by delimiters: ...?
    
    #in which case...if after filtering the original srcTxt_all from the mecab
    #stuff...you're left with
    
    #removed duplicates while preserving order 
    #(can be caused by sentences, multiple forms of the same word, etc)
    colorized_words = list(OrderedDict.fromkeys(colorized_words))
    prons = list(OrderedDict.fromkeys(prons))
    
    #join words together with the designated separator; but give the original src
    #back if lookup failed or if color is turned off
    fields_dest = separator.join(prons)
    
    #determine what/how to return/replace expressions based on the set config 
    delim = config["modification_delimiter"] if config["extend_expressions"] or config["correct_expressions"] else '・'
    if config["correct_expressions"] and not config["is_sentence"]:
        final_src = delim.join(srcTxt_2)
    elif config["extend_expressions"] and not config["is_sentence"]:
        final_src = delim.join(srcTxt_all)
    else:
        final_src = src

    if config["colorFields"] and colorTxt:
        if config["colorFields"] == config["srcFields"]:
            colorTxt = final_src
        if config["color_sentence"]:
            #uncommenting the below ling avoids the 重なるhtml tags problem at the risk of deleting unrelated html
            colorTxt = re.sub(re.escape('&nbsp;'),'', colorTxt)
            colorTxt = soup_maker(colorTxt) 
            #stuff = [word for word in colorized_words] #for testing
            #raise Exception(stuff) #for testing
            #raise Exception(colorTxt)
            count = 0
            for word in colorized_words:
                #raise Exception(re.sub(r'([\>\]])\s','\g<1>',word))
                #raise Exception(re.findall(r'\s?'+re.escape(soup_maker(word)), colorTxt))
                #don't substitute if you're already inside a font color tag
                indices_to_ignore = []
                new_soup = BeautifulSoup(colorTxt, "html.parser")
                tags = [unicode(tag) for tag in new_soup.select("font")]
                tag_lengths = [len(tag) for tag in tags]
                #first remove all text with font tags from the string
                for tag in tags:
                    indices_to_ignore.extend([m.start() for m in re.finditer(re.escape(tag),colorTxt)])
                    #temp = re.sub(re.escape(tag),'', colorTxt)
                #then substitute the new colorized word into the shorter string
                temp = ''
                current_loc = 0
                #if count > 0: raise Exception(indices_to_ignore)
                for start, length, tag in zip(indices_to_ignore, tag_lengths, tags):
                    #raise Exception(colorTxt[current_loc:start])
                    #if re.findall(r'\s?'+re.escape(soup_maker(word)), colorTxt[current_loc:start]):
                    #    if count > 0: raise Exception(colorTxt, re.findall(r'\s?'+re.escape(soup_maker(word)), colorTxt[current_loc:start]))
                    temp += re.sub(r'\s?'+re.escape(soup_maker(word)), re.sub(r'([\>\]])\s','\g<1>',word), colorTxt[current_loc:start])
                    temp += tag
                    current_loc = start+length
                temp += re.sub(r'\s?'+re.escape(soup_maker(word)), re.sub(r'([\>\]])\s','\g<1>',word), colorTxt[current_loc:])
                colorTxt = temp
                if count >20: raise Exception(colorTxt)
                count += 1
                #then add the older font-tagged-text back based on its original index
                #colorTxt = re.sub(r'\s?'+re.escape(soup_maker(word)), re.sub(r'([\>\]])\s','\g<1>',word), colorTxt)
                #sraise Exception(colorTxt)
        else:
            #adds dictionary forms of words to field even if it was already colorized
            if prons and colorized_words: colorTxt = delim.join(colorized_words) 
    if config["colorFields"] == config["srcFields"]:
        final_src = colorTxt
    #else:
    #    final_src = delim.join(srcTxt_all) if config["extend_expressions"] and not config["is_sentence"] else src
    final_color_src = colorTxt    
    #NOTE: colorized_words will only have the words that have prons, and
    #will have them in the form that was able to get a hit, i.e. citation/dictionary form

    if sounds:
        final_snd = sounds
    else:
        final_snd = ''
    
    return final_src, fields_dest, final_color_src, final_snd


# ************************************************
#           Database generation functions        *
# ************************************************
def format_entry(e):
    """ Format an entry from the data in the original database to something that uses html """
    txt = e.midashigo1
    strlen = len(txt)
    acclen = len(e.ac)
    accent = "0"*(strlen-acclen) + e.ac

    # Get the nasal positions
    nasal = []
    if e.nasalsoundpos:
        positions = e.nasalsoundpos.split('0')
        for p in positions:
            if p:
                nasal.append(int(p))
            if not p:
                # e.g. "20" would result in ['2', '']
                nasal[-1] = nasal[-1] * 10

    # Get the no pronounce positions
    nopron = []
    if e.nopronouncepos:
        positions = e.nopronouncepos.split('0')
        for p in positions:
            if p:
                nopron.append(int(p))
            if not p:
                # e.g. "20" would result in ['2', '']
                nopron[-1] = nopron[-1] * 10

    outstr = ""
    overline = False

    for i in range(strlen):
        a = int(accent[i])
        # Start or end overline when necessary
        if not overline and a > 0:
            outstr = outstr + '<span class="overline">'
            overline = True
        if overline and a == 0:
            outstr = outstr + '</span>'
            overline = False

        if (i+1) in nopron:
            outstr = outstr + '<span class="nopron">'

        # Add the character stuff
        outstr = outstr + txt[i]

        # Add the pronunciation stuff
        if (i+1) in nopron:
            outstr = outstr + "</span>"
        if (i+1) in nasal:
            outstr = outstr + '<span class="nasal">&#176;</span>'

        # If we go down in pitch, add the downfall
        if a == 2:
            outstr = outstr + '</span>&#42780;'
            overline = False

    # Close the overline if it's still open
    if overline:
        outstr = outstr + "</span>"

    return outstr


def build_database():
    """ Build the derived database from the original database """
    tempdict = {}
    entries = []

    f = codecs.open(accent_database, 'r', 'utf8')
    for line in f:
        line = re.sub("\{(.*),(.*)\}", "\{\1;\2\}", line.strip())
        line = re.sub("\((.*),(.*)\)", "\(\1;\2\)   ", line.strip())
        entries.append(AccentEntry._make(line.split(",")))
    f.close()

    for e in entries:
        textentry = format_entry(e)

        # A tuple holding both the spelling in katakana, and the katakana with pitch/accent markup
        kanapron = (e.midashigo, textentry)

        # Add expressions for both
        for key in [e.nhk, e.kanjiexpr]:
            if key in tempdict:
                if kanapron not in tempdict[key]:
                    tempdict[key].append(kanapron)
            else:
                tempdict[key] = [kanapron]

    o = codecs.open(derivative_database, 'w', 'utf8')

    for key in tempdict.iterkeys():
        for kana, pron in tempdict[key]:
            o.write("%s\t%s\t%s\n" % (key, kana, pron))

    o.close()


def read_derivative():
    """ Read the derivative file to memory """
    f = codecs.open(derivative_database, 'r', 'utf8')

    for line in f:
        key, kana, pron = line.strip().split("\t")
        kanapron = (kana, pron)
        if key in thedict:
            if kanapron not in thedict[key]:
                thedict[key].append(kanapron)
        else:
            thedict[key] = [kanapron]

    f.close()


# ************************************************
#              Lookup Functions                  *
# ************************************************
def inline_style(txt):
    """ Map style classes to their inline version """

    for key in config["styles"].iterkeys():
        txt = txt.replace(key, config["styles"][key])

    return txt


def getPronunciations(expr):
    """ Search pronuncations for a particular expression """
    ret = []
    if expr in thedict:
        for kana, pron in thedict[expr]:
            inlinepron = inline_style(pron)

            if config["pronunciation_hiragana"]:
                inlinepron = katakana_to_hiragana(inlinepron)

            if inlinepron not in ret:
                ret.append(inlinepron)
    return ret


def lookupPronunciation(expr):
    """ Show the pronunciation when the user does a manual lookup """
    ret = getPronunciations(expr)

    thehtml = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2//EN">
<HTML>
<HEAD>
<style>
body {
font-size: 30px;
}
</style>
<TITLE>Pronunciations</TITLE>
<meta charset="UTF-8" />
</HEAD>
<BODY>
%s
</BODY>
</HTML>
""" % ("<br/><br/>\n".join(ret))

    showText(thehtml, type="html")


def onLookupPronunciation():
    """ Do a lookup on the selection """
    japanese.lookup.initLookup()
    mw.lookup.selection(lookupPronunciation)


# ************************************************
#              Interface                         *
# ************************************************

def createMenu():
    """ Add a hotkey and menu entry """
    if not getattr(mw.form, "menuLookup", None):
        ml = QMenu()
        ml.setTitle("Lookup")
        mw.form.menuTools.addAction(ml.menuAction())

    ml = mw.form.menuLookup
    # add action
    a = QAction(mw)
    a.setText("...pronunciation")
    a.setShortcut("Ctrl+6")
    ml.addAction(a)
    mw.connect(a, SIGNAL("triggered()"), onLookupPronunciation)


def setupBrowserMenu(browser):
    """ Add menu entry to browser window """
    a = QAction("Bulk-add Pronunciations", browser)
    browser.connect(a, SIGNAL("triggered()"), lambda e=browser: onRegenerate(e))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)


def onRegenerate(browser):
    regeneratePronunciations(browser.selectedNotes())


def get_src_dst_fields(fields):
    """ Set source and destination fieldnames """
    src = None
    srcIdx = None
    dst = None
    dstIdx = None
    snd = None
    sndIdx = None
    color = None
    colorIdx = None

    for i, f in enumerate(config["srcFields"]):
        if f in fields:
            src = f
            srcIdx = i
            break

    for i, f in enumerate(config["dstFields"]):
        if f in fields:
            dst = f
            dstIdx = i
            break
            
    for i, f in enumerate(config["sndFields"]):
        if f in fields:
            snd = f
            sndIdx = i
            break
            
    for i, f in enumerate(config["colorFields"]):
        if f in fields:
            color = f
            colorIdx = i
            break

    return src, srcIdx, dst, dstIdx, snd, sndIdx, color, colorIdx

def add_audio(audio):
    sounds = []
    if config["add_sound"] and audio:
        for sound in audio:
            if not isfile(media_folder + os.sep + sound):
                copy(soundFolder + os.sep + sound, media_folder + os.sep + sound)
            sounds.append("[sound:" + sound + "]")
        return ''.join(sounds)

def add_pronunciation_once(fields, model, data, n):
    """ When possible, temporarily set the pronunciation to a field """

    #if "japanese" not in model['name'].lower():
    #    return fields

    src, srcIdx, dst, dstIdx, snd, sndIdx, color, colorIdx = get_src_dst_fields(fields)

    if not src or dst is None:
        return fields
        
    color_src = fields[color] if color else ''
       
    # Only add the pronunciation if there's not already one in the pronunciation field
    if not fields[dst]:
        fields[src], fields[dst], new_color_field, audio = multi_lookup(fields[src], getPronunciations, colorTxt = color_src)
        if snd and audio: fields[snd] = add_audio(audio)
        if color:
            fields[color] = new_color_field
        
    return fields

def add_pronunciation_focusLost(flag, n, fidx):
    # japanese model?
    #if "japanese" not in n.model()['name'].lower():
    #    return flag

    from aqt import mw
    fields = mw.col.models.fieldNames(n.model())

    src, srcIdx, dst, dstIdx, snd, sndIdx, color, colorIdx = get_src_dst_fields(fields)

    if not src or not dst:
        return flag

    # dst field already filled?
    if n[dst]:
        return flag

    # event coming from src field?
    if fidx != srcIdx:
        return flag

    # grab source text
    srcTxt = mw.col.media.strip(n[src])
    if not srcTxt:
        return flag
        
    # grab source text of field to be colorized
    color_src = mw.col.media.strip(n[color]) if color else ''

    # update field
    try:
        n[src], n[dst], new_color_field, audio = multi_lookup(srcTxt, getPronunciations, colorTxt = color_src)
        if snd and audio: n[snd] = add_audio(audio)
        if color:
            n[color] = new_color_field
    except Exception, e:
        raise
    return True


def regeneratePronunciations(nids):
    mw.checkpoint("Bulk-add Pronunciations")
    mw.progress.start()
    for nid in nids:
        note = mw.col.getNote(nid)
        #if "japanese" not in note.model()['name'].lower():
        #    continue

        src, srcIdx, dst, dstIdx, snd, sndIdx, color, colorIdx = get_src_dst_fields(note)

        if not src or dst is None:
            continue

        if note[dst] and not config["regenerate_prons"]:
            # already contains data, skip
            continue

        srcTxt = mw.col.media.strip(note[src])
        if not srcTxt.strip():
            continue
        
        color_src = mw.col.media.strip(note[color]) if color else ''
        
        note[src], note[dst], new_color_field, audio = multi_lookup(srcTxt, getPronunciations, colorTxt = color_src)
        if snd and audio: note[snd] = add_audio(audio)
        if color:
            note[color] = new_color_field
        note.flush()
    mw.progress.finish()
    mw.reset()


# ************************************************
#                   Main                         *
# ************************************************

# First check that either the original database, or the derivative text file are present:
if not os.path.exists(derivative_database) and not os.path.exists(accent_database):
    raise IOError("Could not locate the original base or the derivative database!")

# Generate the derivative database if it does not exist yet
if (os.path.exists(accent_database) and not os.path.exists(derivative_database)) or (os.path.exists(accent_database) and os.stat(thisfile).st_mtime > os.stat(derivative_database).st_mtime):
    build_database()

# If a pickle exists of the derivative file, use that. Otherwise, read from the derivative file and generate a pickle.
if  (os.path.exists(derivative_pickle) and
    os.stat(derivative_pickle).st_mtime > os.stat(derivative_database).st_mtime):
    f = open(derivative_pickle, 'rb')
    thedict = cPickle.load(f)
    f.close()
else:
    read_derivative()
    f = open(derivative_pickle, 'wb')
    cPickle.dump(thedict, f, cPickle.HIGHEST_PROTOCOL)
    f.close()

#fix encoding:
reload(sys)  
sys.setdefaultencoding('utf8')
    
# Create the manual look-up menu entry
createMenu()

from anki.hooks import addHook

addHook("mungeFields", add_pronunciation_once)

addHook('editFocusLost', add_pronunciation_focusLost)

# Bulk add
addHook("browser.setupMenus", setupBrowserMenu)

reader = MecabController()
original_reader = jsupport_mecab()