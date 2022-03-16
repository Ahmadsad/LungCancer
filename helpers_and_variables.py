from nltk.corpus import stopwords
import pandas as pd
from nltk.stem import SnowballStemmer
from sklearn.metrics import roc_auc_score

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
    rowDataFrame = pd.DataFrame(xlwb.Sheets(sheetNum).UsedRange())
    rowDataFrame.columns = rowDataFrame.iloc[0,:]
    return rowDataFrame

def get_cleanedCol_rowData_df(rawDataFrame, columns_toBe_removed=None):
    if columns_toBe_removed is None:
        columns_toBe_removed = ["Diagnos2", "Othercancer","Mutation_FULL", "Stage_gr", "DiagnosticInvestigation","PADdatum",
#                 "STUDY_1","InterviewDate", "Death_date", "DEATH_date_final", "Date_Background", "Intdate_Background",
                                "Lungcancer_Num", "ALL_HISTOLOGIES_ScLC_NScLC_NE", "ALL_HISTOLOGIES", 
                                "ALL_HISTOLOGIES_CompleteOtherCancer", "Other_cancer", "Metastases", 
                                "NoCancer_AdvancedStage_Ordinal", "LC_LCNEC_ejLC_ALL_2017control", "Sensitivity_LC_LCNEC_MM_ejLC", 
                                "BAKGRUND", "BREATHE", "COUGH", "PHLEGM", "PAIN_ACHES_DISCOMFORT", "FATIGUE", "VOICE",
                                "APPETITE_TASTE_EATING", "SMELL", "FEVER", "OTHER_CHANGES", "CURRENT_HEALTH_EORTC"]
        try:
            rawDataFrame = rawDataFrame.drop(labels=columns_toBe_removed, axis=1, inplace=False)
        except:
            rawDataFrame.columns = rawDataFrame.iloc[0,:]
            rawDataFrame = rawDataFrame.drop(labels = columns_toBe_removed, axis=1, inplace=False)
        return rawDataFrame

def get_dates_in_days(rawDataFrame, referens_date_col=None):
    if referens_date_col is None:
        referens_date_col = list(rawDataFrame["InterviewDate"])
    else:
        referens_date_col = list(rawDataFrame[referens_date_col])

    date_cols = get_cols_with_dates(rawDataFrame)
    # put the referense last, to be subtracted lastly
    if referens_date_col[0] in date_cols:
        date_cols.remove(referens_date_col[0])
        date_cols.insert(len(date_cols), referens_date_col[0])

    # get corretly formed date list as reference
    referens_dates_list = get_converted_toCorrect_form_datesList(referens_date_col);

    for date_col in date_cols:
        
        if date_col == "PADdatum":
            current_col = list(rawDataFrame['PADdatum'][1:].astype('str'))
            for idx in range(0, len(current_col)):
                tmp = ""
                for x in current_col[idx].split():
                    if x.isdigit():
                        tmp = tmp + str(x)
                current_col[idx] = tmp    
            rawDataFrame[date_col][1:] = current_col
            
        # get a specific date column in correct form and as list
        dates_list = get_converted_toCorrect_form_datesList(list(rawDataFrame[date_col]));

        for idx in range(1,len(rawDataFrame[date_col])):
            if dates_list[idx] != '#NULL!':
                try:
                    dates_list[idx] =  referens_dates_list[idx] - dates_list[idx];

                except:
                    dates_list[idx] = dates_list[idx]

        rawDataFrame[date_col] = dates_list          
    return rawDataFrame
    
def get_cols_with_dates(rawDataFrame, num_cols=None):
    # other columns with dates but not mentioned in the column name or description
    date_cols = ["Breathe_46", "V3", "V3_Ph_1", "V3_Pain", "V3_Fa_1", "V3_Vo", "V3_Sm", "Fever_2", "Fever_5", "Fever_8",
                        "Fever_11", "Fever_14", "Fever_17", "Fever_20", "Fever_23", "Fever_24", "Otherchanges_2", "Otherchanges_5", 
                        "Otherchanges_8", "Otherchanges_11", "Otherchanges_14", "Otherchanges_17", "Otherchanges_20", "Otherchanges_23",
                        "Otherchanges_26", "Otherchanges_30", "Otherchanges_34", "Otherchanges_38"]
    for col in rawDataFrame.columns:
        if ('date' in col.lower() or 'datum' in col.lower()):
            date_cols.append(col)    
    if num_cols is None:
        return date_cols
    else:
        return date_cols[0:num_cols]
    
def get_converted_toCorrect_form_datesList(dates_list):
    dates_list = list(dates_list)
    for idx in range(1,len(dates_list)):
        if dates_list[idx] != "#NULL!":
            try:
                dates_list[idx] = pd.to_datetime(dates_list[idx], format='%y%m%d', errors='ignore');
                dates_list[idx] = pd.to_datetime(dates_list[idx], errors='ignore');
            except:
                dates_list[idx] = dates_list[idx]
    return dates_list
    

def get_cleaned_dataInfo_df(stringPath):
    dataInfoDF = get_exL_df(stringPath = stringPath, sheetNum = 1)
    dataInfoDF.columns = range(0,len(dataInfoDF.columns))
    dataInfoDF.drop(columns=[1,3], inplace=True)
    dataInfoDF.rename(columns={0: dataInfoDF.iloc[1,0], 2:dataInfoDF.iloc[1,1]}, inplace=True)
    dataInfoDF.drop([0,1,713], axis=0, inplace=True)
    return dataInfoDF
    
    
def get_cleaned_katInfo_df(stringPath):
    katInfoDF = get_exL_df(stringPath = stringPath, sheetNum = 3)
    katInfoDF.columns = range(0,len(katInfoDF.columns))
    katInfoDF.drop(columns=[3], inplace=True)
    katInfoDF.rename(columns={0: "Variable", 1:"Label", 2:"Value"}, inplace=True)
    katInfoDF.drop([0,1], axis=0, inplace=True)
    return katInfoDF

def get_labels_and_indicesOfUnlabeledPatients(rowDataFrame):
    labels = list(rowDataFrame['Lungcancer_Num'])[1:]
    label_list = list()
    removed_indices = list()
    for ind in range(0, len(labels)):
        value = labels[ind]
        if value == 1.0 or value == 2.0:
            label_list.append(value)
        else:
            removed_indices.append(ind+1)
            
    rowDataFrame = rowDataFrame.drop(labels=removed_indices, axis=0, inplace=False)

    return rowDataFrame, label_list, removed_indices

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
    
def get_dict_of_questions_answers(raw_DF, dataInfoDF, katInfoDF, amount_data=None, clear_missings_or_Non=False):
    main_dict = dict()
    tmp_patient_dict = dict()
   
    dict_of_katInfo = get_dict_of_katInfoDF(katInfoDF)
    dict_of_dataInfo = get_dict_of_dataInfoDF(dataInfoDF)
    
    missing_answer = False   
    list_count_removed_features = list()
    
    if amount_data is None or amount_data > len(raw_DF):
        n = len(raw_DF)
    else:
        n = amount_data    
    # dont need patient number as feature
    features = list(raw_DF.columns)[1:]
    for patient_ind in range(1, n):
        ind_ques = 0
        count_removed_features = 0 
        
        ind_ques = 1
        for feature in features:   #range(1, len(raw_DF.iloc[patient_ind,:])):
            # the answer of the patient
            answer = raw_DF.iloc[patient_ind][feature]
            # item = raw_DF.iloc[patient_ind,ind_ques]
            # the question's text instead of only numbers or question name
            value =  dict_of_dataInfo[feature] #  list_of_questions[ind_ques]
            # Remove tags, such as html tags
            if remove_tags(value) is None or remove_tags(value) is "":
                value = ""
            # check if we have categorical info for this specific column name [0, ind_ques], 
            # and replace numbers with corresponding text
            if feature in dict_of_katInfo:
                ques_dict = dict_of_katInfo[feature]
                if str(int(answer)) in ques_dict:
                    # Remove tags, such as html tags and assign the correct text to the corres. number
                    answer = remove_tags(ques_dict[str(int(answer))])
                else: # if missing answer replace with NO/missing
                    answer = "No/missing"
            if (
                answer == '#N/A'or answer == '#N/A!' or 
                answer == '#NULL' or  answer == '#NULL!' or 
                answer == 'None' or answer is None or
                answer == "" or answer == "None/missing" or 
                answer == "No/missing" or answer == -2146826288 or
                "missing" in str(answer) or "NaT" in str(answer)
            ):
                answer = "No/missing"
                missing_answer = True
            # clear questions with no answers, which includes modules such as, Breath, Cough (empty answers, used to seperat modules)
            if clear_missings_or_Non and missing_answer:
                missing_answer = False
                count_removed_features = count_removed_features + 1
                continue
            value = value + ": " + str(answer)
            tmp_patient_dict[feature] = value
            ind_ques = ind_ques + 1
        main_dict[str(int(raw_DF.iloc[patient_ind,0]))] = tmp_patient_dict
        tmp_patient_dict = dict()
        
        # add 2 for the labels at first rows and since pandas aounts from 1 already
        list_count_removed_features.append((patient_ind+2, count_removed_features))
        
    return main_dict, list_count_removed_features

def get_data_list_from_main_dict(main_dict, stemm=True):
    data_list = list()
    for key in main_dict.keys():
        patient_text = list(main_dict[key].values())
        patient_cleaned_text = get_cleaned_list_of_strings(patient_text, stemm=stemm)
        tmp_patient_text = ' '.join(patient_cleaned_text)
        data_list.append(tmp_patient_text)
    return data_list
        
def write_dict_as_json_file(dict_toBe_saved, file_path = None):
    import json
    if file_path is None:
        file_path = "C:/Users/a7mad/Desktop/MEX/PekLung/dict.json"
    # create json object from dictionary
    obj = json.dumps(dict_toBe_saved)
    # open file for writing, "w" 
    f = open(file_path,"w")
    # write json object to file
    f.write(obj)
    # close file
    f.close()
    
def read_dict_from_json_file(file_path=None):
    import json
    if file_path is None:
        file_path = "C:/Users/a7mad/Desktop/MEX/PekLung/dict.json"
    # reading the data from the file
    with open(file_path) as f:
        data = f.read()
    # reconstructing the data as a dictionary
    js = json.loads(data)
    return js

