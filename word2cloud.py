

from wordcloud import WordCloud


def generate(fname, outputf, max_lines=0):
    freq = {}
    line_num = 0
    with open(fname, 'r', encoding='utf-8') as f:
        while (True):
            line = f.readline()
            if (line == '' or (max_lines != 0 and line_num >= max_lines)):
                break;
            line_num += 1
            if (line_num % 100 == 0):
                print('%s lines processed            ' % line_num, end = '\r')
            word_list = line.split(' ')
            for word in word_list:
                if word in freq:
                    freq[word] += 1
                else:
                    freq[word] = 1
        print('%s lines processed            ' % line_num)
    
    wc = WordCloud(font_path = './simkai.ttf', width = 1920, height = 1080, max_font_size = 600, background_color = 'white')
    wc.generate_from_frequencies(freq)
    wc.to_file(outputf)

if __name__ == '__main__':
    generate('dump.txt', 'wordcloud.png')

