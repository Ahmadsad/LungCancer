import re
import string

import numpy as np
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

"""
You might need to run these two guys once to download stopwords and punktations
"""
# nltk.download('stopwords')
# nltk.download('punkt')

stopwords_swedish = stopwords.words('swedish')
__vowels = "aeiouy\xE4\xE5\xF6"
__s_ending = "bcdfghjklmnoprtvy"

__step1_suffixes = ("heterna","hetens","heter","heten","anden","arnas","ernas","ornas"
                    ,"andes","andet","arens","arna","erna","orna","ande","arne","aste"
                    ,"aren","ades","erns","ade","are","ern","ens","het","ast","ad","en"
                    ,"ar","er","or","as","es","at","a","e","s")

__step1_2_suffixes = ("vuxen", "benägen","mogen","omogen","abdomen",
                    "sverige", "maka", "make", "partner", "vecka",
                    "astma", "dålig","början", "ej")

__step2_suffixes = ("dd", "gd", "nn", "dt", "gt", "kt", "tt")
__step3_suffixes = ("fullt", "l\xF6st", "els", "lig", "ig")


__step4_suffix = ("br", "co", "sl", "pa", "q9", "jmf", "11fö", "ing",  'm',  'mm', 'ca', '1fö', 'fö', 'dat',
                  'lu', '1lu','9lu','0','vet','ph','fa','any','gör', 'få', 't', 'ex','f1',' f16', 'rö', 'lu',
                  'sl1sl29', 'ang', '-', 'börj')
# for tfidf:
__step4_suffix1 = ("br", "co", "sl", "pa", "q9", "jmf", "11fö", "ing",  'm',  'mm', 'ca', '1fö', 'fö', 'dat',
                  'lu', '1lu','9lu','0','vet','ph','fa','any','gör', 'få', 't', 'ex','f1',' f16', 'rö', 'lu',
                  'sl1sl29','ang', '-', 'börj', 'år', "datum", "välj", "intervjudatum", 'intervjun','börj', 'ang',
                   'intervju', 'alternativ','fler','tidigare','problem','bäst','sak','känd', 'tyck', 'andr', 'mer',
                   'åren', 'för', 'gång','dag', 'sen', 'minst', 'tex', 'läk', 'sagt', 'vilken vilk','vilken', 'vilk',
                   'beskriv', 'ja','tid', 'tillkommit','jämför','idag','lad','följ','först','ställning','besvär','förändring',
                   'oförändr', 'märk','upplev','gäll', 'haft','ändrat', 'kategorin')

age_choices = ['under40year', '40to65year', '65to85year', 'uver85year']


TAG_RE = re.compile(r'<[^>]+>')
def remove_tags(text):
    return TAG_RE.sub('', text)

def handel_removing_digits(inputString):
    # remove decimals and replace 00 with 0
    if "." in inputString:
        idx = inputString.find(".")
        if has_numbers(inputString[idx+1:idx+2]):
            # print(inputString)
            inputString = inputString[0:idx] + inputString[idx+2:]

    # remove digits in places with qeustion numbers, like Br_01 and so on
    if ('_' in inputString) and has_numbers(inputString):
        # print(inputString)
        inputString = re.sub('[\d_]+', '', inputString)
        # handle sl-sl
        if ('-' in inputString):
            inputString = re.sub('[\D-]+', '', inputString)
    return inputString

def remove_digits_at_start(inputString):
    if len(inputString)<4:
        inputString = re.sub('[\d]+', '', inputString)
    return inputString

def stem(word, without_digits=False, suffix_41=False):
    """
    Stem a Swedish word and return the stemmed form.
    :param word: The word that is stemmed.
    :type word: str or unicode
    :return: The stemmed form.
    :rtype: unicode
    """
    if suffix_41:
        step4_suffix = __step4_suffix1
    else:
        step4_suffix = __step4_suffix

    if word in stopwords_swedish: 
        return ""
    if word=="00" or word=="0":
        return ""
    r1 = _r1_scandinavian(word, __vowels)

    # STEP 1
    for suffix in __step1_suffixes:
        if r1.endswith(suffix):
            if suffix == "s":
                if word[-2] in __s_ending:
                    word = word[:-1]
                    r1 = r1[:-1]
            elif word in __step1_2_suffixes:
                break
            else:
                word = word[: -len(suffix)]
                r1 = r1[: -len(suffix)]
            break

    # STEP 2
    for suffix in __step2_suffixes:
        if r1.endswith(suffix):
            word = word[:-1]
            r1 = r1[:-1]
            break

    # STEP 3
    for suffix in __step3_suffixes:
        if r1.endswith(suffix):
            if suffix in ("els", "lig", "ig"):
                word = word[: -len(suffix)]
            elif suffix in ("fullt", "l\xF6st"):
                word = word[:-1]
            break
            
    # remove question numbers like br_1, br2... and other from suffix 4
    for suffix in step4_suffix:
        if (suffix in word) and (word not in age_choices):
            if word == suffix or has_numbers(word):
                word = ""
                break
    
    if (all(char.isdigit() for char in word)) and (word !='') and (without_digits):
        word = ""

    return word

def _r1_scandinavian(word, vowels):
    """
    Return the region R1 that is used by the Scandinavian stemmers.
    R1 is the region after the first non-vowel following a vowel,
    or is the null region at the end of the word if there is no
    such non-vowel. But then R1 is adjusted so that the region
    before it contains at least three letters.

    :param word: The word whose region R1 is determined.
    :type word: str or unicode
    :param vowels: The vowels of the respective language that are
                used to determine the region R1.
    :type vowels: unicode
    :return: the region R1 for the respective word.
    :rtype: unicode
    :note: This helper method is invoked by the respective stem method of
        the subclasses DanishStemmer, NorwegianStemmer, and
        SwedishStemmer. It is not to be invoked directly!
    """
    r1 = ""
    for i in range(1, len(word)):
        if word[i] not in vowels and word[i - 1] in vowels:
            if 3 > len(word[: i + 1]) > 0:
                r1 = word[3:]
            elif len(word[: i + 1]) >= 3:
                r1 = word[i + 1 :]
            else:
                return word
            break
    return r1

def has_numbers(inputString): 
    return any(char.isdigit() for char in inputString)


### Function to fit the external corpuses
def get_stemmed_corpus(corpus, stemm=False, stemm_by_nltk=False, nltk_lang='swedish', without_digits=False, suffix_41=False):
    if stemm_by_nltk:
        stop = stopwords.words(nltk_lang)
        stemmer = SnowballStemmer(nltk_lang, ignore_stopwords = False)
    punctations = string.punctuation

    corpus_sentenses_tokenized = list()
    for sent in corpus:
        tmp = list()
        sent[0] = remove_digits_at_start(sent[0])
        for word in sent:
            word = word.lower()
            word = handel_removing_digits(word).replace('_', ' ').replace('/',' ')
            word = word.translate(str.maketrans('', '', punctations)).replace('…','').replace('”','')
            
            if stemm:
                word = stem(word, without_digits=without_digits, suffix_41=suffix_41)
            if word:
                tmp.append(word)
        words = tmp

        if stemm_by_nltk:
            words = [stemmer.stem(word) for word in words if word not in stop]

        if words:
            corpus_sentenses_tokenized.append(words)

    return corpus_sentenses_tokenized

def get_data_from_main_dict(main_dict, stemm=True, return_corpus_sent=False, return_corpus_token=False, without_digits=False, suffix_41=False):
    from nltk import word_tokenize
    data_list = list()
    corpus_sentenses = list()
    corpus_sentenses_tokenized = list()

    for key in main_dict.keys():
        patient_text = list(main_dict[key].values())
        patient_cleaned_text = get_cleaned_list_of_strings(patient_text, stemm=stemm, without_digits=without_digits,
                                                           suffix_41=suffix_41)
        
        if return_corpus_sent or return_corpus_token:
            for sent in patient_cleaned_text:
                if return_corpus_sent:
                    corpus_sentenses.append(sent)
                    
                if return_corpus_token:
                    temp = list()
                    for word in word_tokenize(sent):
                            temp.append(word)
                    corpus_sentenses_tokenized.append(temp)
                    
        tmp_patient_text = ' '.join(patient_cleaned_text)
        data_list.append(tmp_patient_text)
    return data_list, corpus_sentenses, corpus_sentenses_tokenized

def get_cleaned_list_of_strings(listOfStrings, stemm=False, stemm_by_nltk=False, nltk_lang='swedish', without_digits=False, suffix_41=False):
    if stemm_by_nltk:
        stop = stopwords.words(nltk_lang)
        stemmer = SnowballStemmer(nltk_lang, ignore_stopwords = False)
    
    punctations = string.punctuation.replace('-','')
    output_text = list()
    for text in listOfStrings:
        if text is None: 
            text = ''
        words = re.split("\s|/|_|[,.]", text)
        words[0] = remove_digits_at_start(words[0])
        tmp = list()
        for word in words:
            word = word.lower()
            word = handel_removing_digits(word).replace('_', ' ').replace('/',' ')
            word = word.translate(str.maketrans('', '', punctations)).replace('…','').replace('”','')

            if stemm and word:
                word=stem(word, without_digits=without_digits, suffix_41=suffix_41)
                if word:
                    tmp.append(word)
            elif not stemm:
                tmp.append(word)

        words = tmp
        if stemm_by_nltk:
            words = [stemmer.stem(word) for word in words if word not in (stop)]

        if words:
            words = " ".join(words)
            output_text.append(words)
    return output_text