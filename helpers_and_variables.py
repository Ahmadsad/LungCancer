from nltk.corpus import stopwords
import pandas as pd
from nltk.stem import SnowballStemmer

import win32com.client as win32
import string
import numpy as np
import re


xlApp = win32.Dispatch("Excel.Application")


stopwords = stopwords.words('swedish')
punctations = string.punctuation

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

# remove question numbers like br_1, br2...
__step4_suffix = ("br", "co", "sl", "pa")

TAG_RE = re.compile(r'<[^>]+>')

def remove_tags(text):
    return TAG_RE.sub('', text)

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
    
def stem(word):
    """
    Stem a Swedish word and return the stemmed form.

    :param word: The word that is stemmed.
    :type word: str or unicode
    :return: The stemmed form.
    :rtype: unicode

    """
    word = word.lower()
    
#     print(stopwords)
    
    if word in stopwords: 
        return word
    
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
            
# remove question numbers like br_1, br2...
    for suffix in __step4_suffix:
        if suffix in word:
            indx = word.index(suffix)
            if word == suffix or has_numbers(word):
                word = ""
                break;
        
    return word

def has_numbers(inputString): 
    return any(char.isdigit() for char in inputString)

def remove_digits_at_start(inputString):
    if has_numbers(inputString[0:3]):
        if " " in inputString:
            inputString = inputString[inputString.index(" ")+1:]
    return inputString

def get_exL_df(stringPath, password=None, sheetNum=0):
    if password is not None:
        xlwb = xlApp.Workbooks.Open(stringPath, False, True, None, password)
    else:
        xlwb = xlApp.Workbooks.Open(stringPath, False, True, None)
    return pd.DataFrame(xlwb.Sheets(sheetNum).UsedRange())

def get_cleaned_dataInfo_df(stringPath):
    dataInfoDF = get_exL_df(stringPath = stringPath, sheetNum = 1)
    dataInfoDF.drop(columns=[1,3], inplace=True)
    dataInfoDF.rename(columns={0: dataInfoDF.iloc[1,0], 2:dataInfoDF.iloc[1,1]}, inplace=True)
    dataInfoDF.drop([0,1,713], axis=0, inplace=True)
    return dataInfoDF
    
    
def get_cleaned_katInfo_df(stringPath):
    katInfoDF = get_exL_df(stringPath = stringPath, sheetNum = 3)
    katInfoDF.drop(columns=[3], inplace=True)
    katInfoDF.rename(columns={0: "Variable", 1:"Label", 2:"Value"}, inplace=True)
    katInfoDF.drop([0,1], axis=0, inplace=True)
    return katInfoDF

    
def get_dict_of_dataInfoDF(dataFrame):
    _dict = dict()
    list_of_questions = dataFrame['Label'].tolist()
    list_of_quesNams = dataFrame['Variable'].tolist()
    ind = 0
    for question in list_of_questions:
        _dict[list_of_quesNams[ind]] = question
        ind=ind+1
    return _dict

def get_dict_of_katInfoDF(dataFram):
    dict_of_katInfo = dict()
    list_of_vars = dataFram['Variable'].tolist()
    list_of_labels = dataFram['Label'].tolist()
    list_of_values = dataFram['Value'].tolist()
    count = 0
    for i in range(0,len(list_of_vars)):
        tmp_lbl_value_dict = dict()
        if list_of_vars[i] is not None or i == len(list_of_vars)-1:
            if count == 0:
                tmp_lbl_value_dict[list_of_labels[i]] = list_of_values[i]
            else:
                if i == len(list_of_vars)-1:
                    for idx in range(i-count, i+1):    
                        tmp_lbl_value_dict[list_of_labels[idx]] = list_of_values[idx]
                else:
                    for idx in range(i-count, i):    
                        tmp_lbl_value_dict[list_of_labels[idx]] = list_of_values[idx]
            key = list_of_vars[i-count]
            count = 1
        elif list_of_vars[i] is None:
            count = count + 1
        if count == 1:
            dict_of_katInfo[key] = tmp_lbl_value_dict
    return dict_of_katInfo

def get_cleaned_list_of_strings(listOfStrings, stemm = False, stemm_by_nltk=False):
    stemmer = SnowballStemmer("swedish", ignore_stopwords = True)
    output_text = list()
    for text in listOfStrings:
        if text is None: 
            text = 'No/missing'
#         if type(text) is not list:
#             text = list(text)
        text = text.replace('/',' ').replace('…','').replace('”','').replace('_',' ')
        words = text.lower().translate(str.maketrans('', '', punctations))
        words = remove_digits_at_start(words)
        words = words.split()
        words_without_stopwords = [word for word in words if word not in stopwords]
        words = words_without_stopwords
        if stemm:
            words = [stem(word) for word in words_without_stopwords]
        elif stemm_by_nltk:
            words = [stemmer.stem(word) for word in words_without_stopwords]
        text_without_stopwords = " ".join(words)
        output_text.append(text_without_stopwords)
    return output_text

def get_array_of_words(listOfStrings):
    _list = list()
    for text in listOfStrings:
        text = text.lower()
        sentences = text.split()
        for words in sentences:
            word = words.split()
            _list.append(word)
    _list = np.array(_list)
    word_array = np.empty(shape=len(_list), dtype=object)
    for x in range(len(_list)):
        word_array[x] = _list[x][0]
    return word_array

def get_stemmed_strings_as_nltk_SnowballStemmer(listOfStrings, ignore_stopwords = True):
    from nltk.stem import SnowballStemmer
    stemmer = SnowballStemmer("swedish", ignore_stopwords = ignore_stopwords)
    output_text_after_Stem = list()

    for text in listOfStrings:
        words = text.split()
        words_after_stem = [stemmer.stem(word) for word in words]
        text_after_stem = " ".join(words_after_stem)
        output_text_after_Stem.append(text_after_stem)
        
    return output_text_after_Stem

def get_tokenized_strings_by_nltk(listOfStrings):
    from nltk import word_tokenize
    output_words_after_tokenize = list()

    for text in listOfStrings:
        words = text.split()
        words_after_tokenize = [word_tokenize(word) for word in words]
        for word in words_after_tokenize:
            output_words_after_tokenize.append(word)

    return output_words_after_tokenize
    
def get_dict_of_questions_answers(row_DF, dataInfo_DF, katInfoDF, amount_data=None):
    main_dict = dict()
    tmp_patient_dict = dict()
    list_of_questions = dataInfo_DF['Label'].tolist()
    list_of_quesNams = dataInfo_DF['Variable'].tolist()
    dict_of_katInfo = get_dict_of_katInfoDF(katInfoDF)
    
    if amount_data is None or amount_data > len(row_DF):
        n=len(row_DF)
    else:
        n = amount_data    
        
    for row in range(1, len(row_DF)):
        ind_ques = 0
        for ind_ques in range(0, len(row_DF.iloc[row,:])):
            item = row_DF.iloc[row,ind_ques]
            value = list_of_questions[ind_ques]
            if remove_tags(list_of_questions[ind_ques]) is None or remove_tags(list_of_questions[ind_ques]) is "":
                value = ""
    #         if type(item) is float: item = int(item)
            if row_DF.iloc[0, ind_ques] in dict_of_katInfo:
                ques_dict = dict_of_katInfo[row_DF.iloc[0, ind_ques]]
                if str(int(item)) in ques_dict:
                    item = ques_dict[str(int(item))]
                else: # missing answer
                    item = "No/missing"
            if item == '#NULL' or item == '#N/A'or item == '#N/A!' or item == '#NULL!' or item == 'None' or item is None:
                item = "No/missing"

            value = value + ": " + str(item)
            tmp_patient_dict[list_of_quesNams[ind_ques]] = value

        main_dict[str(int(row_DF.iloc[row,0]))] = tmp_patient_dict
        tmp_patient_dict = dict()
    return main_dict