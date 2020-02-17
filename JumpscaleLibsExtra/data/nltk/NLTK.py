from Jumpscale import j

try:
    import nltk
    from nltk.tokenize import wordpunct_tokenize
except:
    pass
j.builders.runtimes.python3.pip_package_install("nameparser")
from nameparser.parser import HumanName
from pprint import pprint as print
from unidecode import unidecode

# https://pypi.python.org/pypi/transliterate

VOWELS_ORD = [97, 101, 105, 111, 117, 121]
CHARS_NONVOWEL = {
    98: 0,
    99: 1,
    100: 2,
    102: 3,
    103: 4,
    104: 5,
    106: 6,
    107: 7,
    108: 8,
    109: 9,
    110: 10,
    112: 11,
    113: 12,
    114: 13,
    115: 14,
    116: 15,
    118: 16,
    119: 17,
    120: 18,
    122: 19,
}
NUMBERS = {48: 0, 49: 1, 50: 2, 51: 3, 52: 4, 53: 5, 54: 6, 55: 7, 56: 8, 57: 9}
NONVOWELS_ORD = [item for item in CHARS_NONVOWEL.keys()]


class NLTKFactory(j.baseclasses.object):

    __jslocation__ = "j.data.nltk"

    def install(self):
        j.builders.runtimes.python3.pip_package_install("nltk, nameparser, unidecode")
        self.download_nltk()

    def download_nltk(self):
        nltk.download("punkt")
        nltk.download("averaged_perceptron_tagger")
        nltk.download("maxent_ne_chunker")
        nltk.download("words")

    def human_names_get(self, text, unidecode=True):
        if unidecode:
            text = self.unidecode(text)
        tokens = nltk.tokenize.word_tokenize(text)
        pos = nltk.pos_tag(tokens)
        sentt = nltk.ne_chunk(pos, binary=False)
        person_list = []
        person = []
        name = ""
        for subtree in sentt.subtrees(filter=lambda t: t.label() == "PERSON"):
            for leaf in subtree.leaves():
                person.append(leaf[0])
            if len(person) > 1:  # avoid grabbing lone surnames
                for part in person:
                    name += part + " "
                if name[:-1] not in person_list:
                    person_list.append(name[:-1])
                name = ""
            person = []

        return person_list

    def unidecode(self, text, lowercase=False):
        """
        go from unicode to text
        """
        text = text.replace("'", "")
        text = text.replace("`", "")
        text = unidecode(text)
        if lowercase:
            text = text.lower()
        return text.strip()

    def dense(self, text, keepnumbers=True, remove_vowels=False, removespaces=False, word_minsize=4):
        # print(text)
        text = self.unidecode(text)
        text = text.lower()
        state = ""
        word = ""
        res = []
        lword = 0

        # import pudb; pudb.set_trace()
        for char in text:
            o = ord(char)
            if keepnumbers and o > 47 and o < 58:
                # is number
                state = "N"
                word += char
                continue
            if state == "N" and word != "":
                if not (o > 96 or o < 123) or (o > 31 and o < 48):
                    # means we are at end of number and there is no letter after it
                    res.append(word)
                    word = ""
                    state = ""
                    lword = 0
                    continue
                else:
                    state = ""
            if o > 96 and o < 123:
                # ascci char
                lword += 1
                if remove_vowels and o in VOWELS_ORD:
                    continue
                word += char
                continue

            if lword > word_minsize - 1:
                res.append(word)

            word = ""
            state = ""
            lword = 0

        # the last one
        if lword > word_minsize - 1:
            res.append(word)

        if removespaces:
            r = "".join(res)
        else:
            r = " ".join(res)

        r = r.strip()
        return r

    # def dense(self,text,removespaces=False,word_minsize=4,keepnumbers=True,remove_vowels=True):
    #     """
    #     go to ascii, lower case
    #     remove all vowels
    #     """
    #     # text=self.unidecode(text)
    #     # if word_minsize!=None:
    #     #     splitted=text.split(" ")
    #     #     if len(splitted)>1:
    #     #         res=[item for item in splitted if len(item)>word_minsize]
    #     #         text=" ".join(res)

    #     text=self.nonascii_letters_remove(text,unidecode=True,keepnumbers=keepnumbers,remove_vowels=remove_vowels,removespaces=removespaces)

    #     return text

    def dense_binary(self, text, removespaces=False):
        text = self.dense(text, removespaces=removespaces)
        res = []
        for item in text:
            res.append(ord(item))
        return bytes(res)

    def stem(self, text, processnames=True):
        """
        bring words back to normal

        return persons, text
        """
        res = []
        stemmer = nltk.PorterStemmer()
        text = self.unidecode(text)
        if processnames:
            names = self.human_names_get(text, unidecode=False)
            for name in names:
                text = text.replace(name, "")
        text = text.lower()
        for item in wordpunct_tokenize(text):

            item = self.dense(item)
            item = stemmer.stem(item)
            item = item.strip()
            if item != "":
                res.append(item)
        if processnames:
            return names, " ".join(res)
        else:
            return " ".join(res)

    def test(self):
        """
        js_shell 'j.data.nltk.test()'
        """

        self.install()

        text = """
            Some economists have responded positively to Bitcoin, including
            Francois R. Velde, senior economist of the Federal Reserve in Chicago :
            who described it as "an elegant solution to the problem of creating a
            digital currency." In November 2013 Richard Branson announced that
            Virgin Galactic would accept Bitcoin as payment, saying that he had invested
            in Bitcoin and found it "fascinating how a whole new global currency
            has been created", encouraging Antonín Dvořák others to also invest in Bitcoin.
            Other economists commenting on Bitcoin have been critical.
            Economist Paul Krugman has suggested that the structure of the currency
            incentivizes hoarding and that its value derives from the expectation that
            others will accept it as payment. Economist Larry Summers has expressed
            a "wait and see" attitude René Magritte when it comes to Bitcoin. Nick Colas, a market
            strategist for ConvergEx Group, has remarked on the effect of increasing
            use of Bitcoin and its restricted supply, noting, "When incremental """

        print(self.stem(text))

        print(self.human_names_get(text))

        print(self.unidecode("ko\u017eu\u0161\u010dek"))
        print(self.unidecode("René Magritte"))
        print(self.unidecode("Antonín Dvořák"))

        print(self.dense("ko\u017eu\u0161\u010dek"))
        print(self.dense("Antonín Dvořák"))

        r = self.dense("1Antonín 20 Dvořák1", keepnumbers=True, remove_vowels=False)
        print(r)
        assert r == "1antonin 20 dvorak1"

        r = self.dense("1Antonín Dvořák1", keepnumbers=False, remove_vowels=False)
        print(r)
        assert r == "antonin dvorak"

        r = self.dense("1Antonín Dvořák1", keepnumbers=False, remove_vowels=True)
        print(r)
        assert r == "ntnn dvrk"

        r = self.dense("1Antonín Dvořák1", keepnumbers=False, remove_vowels=True, removespaces=True)
        print(r)
        assert r == "ntnndvrk"

        r = self.dense(" departments 1962 the cruelty upon", removespaces=False, remove_vowels=True)
        print(r)
        assert r == "dprtmnts 1962 crlt pn"

        j.tools.timer.start("dense_binary")
        nr = 50000
        for i in range(nr):
            self.dense_binary("1Antonín Dvořák1")
        j.tools.timer.stop(nr)
