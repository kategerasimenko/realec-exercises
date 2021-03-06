import sys, codecs, re, os
from collections import defaultdict

class Exercise:
    def __init__(self, path_new, path_old):
        self.path_new = path_new
        self.path_old = path_old
        self.exercises_out = os.makedirs('moodle_exercises', exist_ok = True)
        # Possible variants of lex errors: ['Word_choice', 'lex_item_choice', 'Often_confused', 'Choice_synonyms',
        #                'lex_part_choice', 'Absence_comp_colloc', 'Redundant', 'Derivation',
        #                'Conversion', 'Formational_affixes', 'Suffix', 'Prefix', 'Category_confusion']
        self.error_type = ['Word_choice']
        self.current_doc_errors = defaultdict()

    def find_errors_indoc(self, line):
        """
        Find all T... marks and save in dictionary.
        Format: {"T1":{'Error':err, 'Index':(index1, index2), "Wrong":text_mistake}}
        """
        if re.search('^T', line) is not None and 'pos_' not in line:
            try:
                t, span, text_mistake = line.strip().split('\t')
                err, index1, index2 = span.split()
                self.current_doc_errors[t] = {'Error':err, 'Index':(index1, index2), "Wrong":text_mistake}
            except:
                print("Something wrong! No Notes probably", line)

    def find_answers_indoc(self, line):
        if re.search('^#', line) is not None and 'lemma =' not in line:
            try:
                number, annotation, correction = line.strip().split('\t')
                t_error = annotation.split()[1]
                if self.current_doc_errors.get(t_error):
                    self.current_doc_errors[annotation.split()[1]]['Right'] = correction
            except:
                print("Something wrong! No Notes probably", line)


    def find_delete_seqs(self, line):
        if re.search('^A', line) is not None and 'Delete' in line:
            t = line.strip().split('\t')[1].split()[1]
            if self.current_doc_errors.get(t):
                self.current_doc_errors[t]['Delete'] = 'True'

    def find_sentences(self):
        """ Collect errors info """
        anns = [f for f in os.listdir(self.path_old) if f.endswith('.ann')]
        for ann in anns:
            print(ann)
            with open(self.path_old + ann, 'r', encoding='utf-8') as ann_file:
                for line in ann_file.readlines():
                    self.find_errors_indoc(line)
                    self.find_answers_indoc(line)
                    self.find_delete_seqs(line)
            self.make_one_exercise(ann.split('.')[0])
            self.current_doc_errors.clear()

    def make_one_exercise(self, filename):
        """

        :param filename: name of the textfile
        """
        with open(self.path_new+filename+'.txt', 'a', encoding='utf-8') as new_file:
            with open(self.path_old+filename+'.txt', 'r', encoding='utf-8') as text_file:
                one_text = text_file.read()
                for i, sym in enumerate(one_text):
                    for t_key, dic in self.current_doc_errors.items():
                        if dic.get('Index')[0] == str(i):
                            if dic.get('Right'):
                                indexes_comp = int(dic.get('Index')[1]) - int(dic.get('Index')[0])
                                if dic.get('Error') in self.error_type:
                                    new_file.write("*"+str(dic.get('Right'))+'*'+str(indexes_comp)+'*')
                                else:
                                    new_file.write(dic.get('Right') +
                                                   '#'+str(indexes_comp)+ '#')
                            else:
                                if dic.get('Delete'):
                                    indexes_comp = int(dic.get('Index')[1]) - int(dic.get('Index')[0])
                                    new_file.write("#DELETE#"+str(indexes_comp)+"#")
                    new_file.write(sym)

    def short_answer(self, new_text):
        good_sentences = []
        sentences = [''] + new_text.split('. ')
        for sent1, sent2, sent3 in zip(sentences,sentences[1:], sentences[2:]):
            if '*' in sent2:
                try:
                    sent, right_answer, index, other = sent2.split('*')
                    wrong = other[:int(index)]
                    new_sent = sent + '<b>' + wrong + '</b>' + other[int(index):] + '.'
                    text = sent1+'. '+new_sent+' '+sent3
                    if '*' not in text:
                         good_sentences.append((text, right_answer))
                except:
                    print("Bad: ", sent2)

        return good_sentences


    def write_sh_answ_exercise(self, sentences):
        pattern = '<question type="shortanswer">\n\
                    <name>\n\
                    <text>Vocabulary realec</text>\n\
                     </name>\n\
                <questiontext format="html">\n\
                <text><![CDATA[{}]]></text>\n\
             </questiontext>\n\
        <answer fraction="100">\n\
        <text><![CDATA[{}]]></text>\n\
        <feedback><text>Correct!</text></feedback>\n\
        </answer>\n\
        </question>\n'
        with open('ielts_Word_choice_new.xml', 'a', encoding='utf-8') as moodle_ex:
            moodle_ex.write('<quiz>\n')
            for ex in sentences:
                moodle_ex.write((pattern.format(ex[0], ex[1])).replace('&','and'))
            moodle_ex.write('</quiz>')
        with open('ielts_Word_choice_new.txt', 'a', encoding='utf-8') as plait_text:
            for ex in sentences:
                plait_text.write(ex[1]+'\t'+ex[0]+'\n\n')


    def make_moodle_format(self, type='find_error'):
        """
        Write it all in moodle format
        :param type: find_error or word_bank
        """
        all_sents = []
        for f in os.listdir(self.path_new):
            new_text = ''
            print(f)
            with open(self.path_new + f,'r', encoding='utf-8') as one_doc:
                text_array = one_doc.read().split('#')
                current_number = 0
                for words in text_array:
                    words = words.replace('\n', ' ').replace('\ufeff', '')
                    if re.match('^[0-9]+$', words):
                        if words != '':
                            current_number = int(words)
                    elif words == 'DELETE':
                        current_number = 0
                    else:
                        new_text += words[current_number:]
                        current_number = 0
            if '*' in new_text:
                all_sents += self.short_answer(new_text)
        self.write_sh_answ_exercise(all_sents)



if __name__ == "__main__":

    path_new, path_old = './new_texts/', './IELTS2015/'
    e = Exercise(path_new, path_old)
    e.find_sentences()

    e.make_moodle_format()
