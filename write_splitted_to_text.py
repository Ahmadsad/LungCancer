import os
import re
from bs4 import BeautifulSoup


def main():
    files_path = r"C:/Users/a7mad/Desktop/MEX/PekLung/saved_stuff/corpus/split/splitted_files"

    text_file_path = r"C:/Users/a7mad/Desktop/MEX/PekLung/saved_stuff/corpus/split/splitted_text_files"

    paths = os.listdir(files_path)
    i = 0
    for path in paths:
        xml_file_path = files_path + r'/'+ path
        with open(xml_file_path, 'r', encoding="utf8") as f:
            file = f.read() 
        soup = BeautifulSoup(file, 'xml')
        del file
        articles = soup.find_all('p')
        del soup
        text_file = text_file_path + '/' + str(i) + ".txt"
        f = open(text_file,"w")
        f.close()
        del f
        f = open(text_file, 'a')
        for article in articles:
            text = re.sub('<[^<]+>', "", str(article)) + " "
            try:
                f.write(text)
            except:
                print("failed once at %d " %i)
            del text, article
        f.close()
        i =i+1
        del articles

        print("part %d Done" % i)

if __name__ == "__main__":
    main()