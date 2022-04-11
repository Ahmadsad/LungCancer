import os
import re
import string
import nltk
import gensim
from gensim.models import Word2Vec
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer


def text_to_sentences(text_string):
    text_string = text_string.replace("\n", " ")
    characters_to_remove = [",",";","'s", "@", "&","*", 
    "(",")","#","!","%","=","+","-","_",":", '"',"'"]
    for item in characters_to_remove:
        text_string = text_string.replace(item,"")
    characters_to_replace = ["?"]
    for item in characters_to_replace:
        text_string = text_string.replace(item,".")

    sentences = text_string.split(".")
    j = 0; 
    tokenized_sentences = list()
    for sentence in sentences:
        if len(sentence) <= 3:
            pass
        elif sentence[0] == " ":
            sentence = sentence[1:]
            # sentences[j] = sentence;
            stemmed_sentence = stemming(sentence)
            tokenized_sentences.append(stemmed_sentence)
            j += 1
        else:
            # sentences[j] = sentence;
            stemmed_sentence = stemming(sentence)
            tokenized_sentences.append(stemmed_sentence)
            j += 1

    return(tokenized_sentences)

def stemming(sentence):
    punctations = string.punctuation
    stop = stopwords.words('swedish')
    stemmer = SnowballStemmer('swedish', ignore_stopwords = False)
    tmp = list()
    for word in sentence.split():
        word = word.lower().replace('_', ' ').replace('/',' ').translate(str.maketrans('', '', punctations)).replace('…','').replace('”','')
        if word:
            tmp.append(word)
    sentence = [stemmer.stem(word) for word in tmp if word not in stop]
    tmp = list()
    for word in sentence:
        if word:
            tmp.append(word)
    sentence = tmp
    return sentence

def main():
    text_file_path = r"C:/Users/a7mad/Desktop/MEX/PekLung/saved_stuff/corpus/split/splitted_text_files"

    paths = os.listdir(text_file_path)
    i = 0
    file_path_model =r"C:/Users/a7mad/Desktop/MEX/PekLung/wiki_word2vec.model"
    own_model = Word2Vec.load(file_path_model)
    file_path_vectors =r"C:/Users/a7mad/Desktop/MEX/PekLung/wiki_word2vec.wordvectors"

    for path in paths:
        text_file = text_file_path + r'/' + path
        with open(text_file, 'r') as f:
            text = f.read()
        tokenized_sentences = text_to_sentences(text)
        own_model.train(tokenized_sentences, total_examples=len(tokenized_sentences), epochs=own_model.epochs)
        del tokenized_sentences, text_file, text
        own_word_vectors = own_model.wv

        own_model.save(file_path_model)
        own_word_vectors.save(file_path_vectors)
        del own_word_vectors

        print("part %d Done" % i)


if __name__ == "__main__":
    main()
