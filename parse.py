import re
from enum import Enum
from subprocess import call
from functools import reduce

from docopt import docopt

# 定义三个枚举类
# 定义表状态
class TABLE(Enum):
    Init = 1
    Format = 2
    Table = 3

# 有序序列状态
class ORDERLIST(Enum):
    Init = 1
    List = 2

# 快状态
class BLOCK(Enum):
    Init = 1
    Block = 2
    CodeBlock = 3

# 定义全局状态，并初始化状态
table_state = TABLE.Init
orderList_state = ORDERLIST.Init
block_state = BLOCK.Init
is_code = False
is_normal = True

temp_table_first_line = []
temp_table_first_line_str = ""



def parse(input):
    global block_state, is_normal
    is_normal = True
    result = input

    # 检测当前 input 解析状态
    result = text_state(input)

    if block_state == BLOCK.Block:
        return result
    # 分析标题标记 #
    title_rank = 0
    for i in range(6, 0, -1):
        if input[:i] == '#'*i:
            title_rank = i
            break
    if title_rank != 0:
        #处理标题，转化为相应的 HTMl 文本
        result = handleTitle(input, title_rank)
        return result

    # 分析分割线标记
    if len(input) > 2 and all_same(input[:-1], '-') and input[-1] == '\n':
        result = "<hr>"
        return result
    
    # 解析无序列表
    unorderd = ['+', '-']
    if result != "" and result[0] in unorderd:
        result = handleUnorderd(result)
        is_normal = False

    f = input[0]
    count = 0
    sys_q = False
    while f == '>':
        count += 1
        f = input[count]
        sys_q = True
    if sys_q:
        result = "<blockquote style=\"color:#8fbv8f\"> "*count + "<b>" +input[count:] + "</b>" + "</blockquote>"*count
        is_normal = False

    # 处理特殊标记 ,比如 *** ,~~~
    result =tokenHandler(result)
    # END

    # 解析图像链接
    result = link_image(result)
    pa = re.compile(r'^(\s)*$')
    a = pa.match(input)
    if input[-1] == "\n" and is_normal == True and not a:
        result+="</br>"

    return result




def text_state(input):
    global table_state, orderList_state, block_state, is_code, temp_table_first_line,temp_table_first_line_str
    Code_List = ["python\n", "c++\n", "c\n"]

    result = input
    
    # 构建正则表达式规则
    # 匹配块标识
    pattern = re.compile(r'```(\s)*\n')
    a = pattern.match(input)

    # 普通块
    if a and block_state == BLOCK.Init:
        result = "<blockquote>"
        block_state = BLOCK.Block
        is_normal = False
    # 特殊代码块
    elif len(input) > 4 and input[0:3] == '```' and (input[3:9] == "python" or input[3:6] == "c++" or input[3:4]=="c") and block_state == BLOCK.Init:
        block_state = BLOCK.Block
        result = "<code></br>"
        is_code = True
        is_normal = False
    # 块结束
    elif block_state == BLOCK.Block and input == "```\n":
        if is_code:
            result = "</code>"
        else:
            result = "</blockquote>"
        block_state = BLOCK.Init
        is_code = False
        is_normal = False
    elif block_state == BLOCK.Block:
        pattern = re.compile(r'[\n\r\v\f\ ]')
        result = pattern.sub("&nbsp", result)
        pattern = re.compile(r'\t')
        result = pattern.sub("&nbsp"*4, result)
        result = "<span>" + result + "</span></br>"
        is_normal = False

    # 解析有序序列
    if len(input) >2 and input[0].isdigit() and input[1] == '.' and orderList_state == ORDERLIST.Init:
        orderList_state = ORDERLIST.List
        result = "<ol><li>" + input[2:] + "</li>"
        is_normal = False
    elif len(input) >2 and input[0].isdigit() and input[1] == '.' and orderList_state == ORDERLIST.List:
        result = "<li>" + input[2:] + "</li>"
        is_normal = False
    elif orderList_state == ORDERLIST.List and (len(input) <= 2 or input[0].isdigit() == False or input[1] != '.'):
        result = "</ol>" +input
        orderList_state = ORDERLIST.Init

    # 解析表格
    pattern = re.compile(r'^((.+)\|)+((.))$')
    match = pattern.match(input)
    if match:
        l = input.split('|')
        l[-1] = l[-1][:-1]
        # 将空字符弹出列表
        if l[0] == '':
            l.pop(0)
        if l[-1] == '':
            l.pop(-1)
        if table_state == TABLE.Init:
            table_state = TABLE.Format
            temp_table_first_line = 1
            temp_table_first_line_str = input
            result = ""
        elif table_state == TABLE.Format:   
            # 如果是表头与表格主题的分割线
            if reduce(lambda a, b: a and b, [all_sam(i,'-') for i in l], True):
                table_state = TABLE.Table
                result = "<table><thread><tr>"
                is_normal = False

                # 添加表头
                for i in temp_table_first_line:
                    result += "<th>" + i + "</th>"
                result += "</tr>"
                result += "</thread><tbody>"
                is_normal = False
            else:
                result = temp_table_first_line_str + "</br>" + input
                table_state = TABLE.Init

        elif table_state == TABLE.Table:
            result = "<tr>"
            for i in l:
                result += "<td>" + i + "</td>"
            result += "</tr>"

    elif table_state == TABLE.Table:
        table_state = TABLE.Init
        result = "</tbody></table>" + result
    elif table_state == TABLE.Format:
        pass
    
    return result


#　判断 lst 是否全由字符 sym 构成　
def all_same(lst, sym):
    return not lst or sym * len(lst) == lst

# 处理标题
def handleTitle(s, n):
    temp = "<h" + repr(n) + ">" + s[n:] + "</h" + repr(n) + ">"
    return temp

# 处理无序列表
def handleUnorderd(s):
    s = "<ul><li>" + s[1:]
    s += "</li></ul>"
    return s


def tokenTemplate(s, match):
    pattern = ""
    if match == '*':
        pattern = "\*([^\*]*)\*"
    if match == '~~':
        pattern = "\~\~([^\~\~]*)\~\~"
    if match == '**':
        pattern = "\*\*([^\*\*]*)\*\*"
    return pattern

# 处理特殊标识，比如 **, *, ~~
def tokenHandler(s):
    l = ['b', 'i', 'S']
    j = 0
    for i in ['**', '*', '~~']:
        pattern = re.compile(tokenTemplate(s,i))
        match = pattern.finditer(s)
        k = 0
        for a in match:
            if a:
                content = a.group(1)
                x,y = a.span()
                c = 3
                if i == '*':
                    c = 5
                s = s[:x+c*k] + "<" + l[j] + ">" + content + "</" + l[j] + ">" + s[y+c*k:]
                k += 1
        pattern = re.compile(r'\$([^\$]*)\$')
        a = pattern.search(s)
        if a:
            global need_mathjax
            need_mathjax = True
        j += 1
    return s


# 处理链接
def link_image(s):
    # 超链接
    pattern = re.compile(r'\\\[(.*)\]\((.*)\)')
    match = pattern.finditer(s)
    for a in match:
        if a:
            text, url = a.group(1,2)
            x, y = a.span()
            s = s[:x] + "<a href=" + url + " target=\"_blank\">" + text + "</a>" + s[y:]

    # 图像链接
    pattern = re.compile(r'!\[(.*)\]\((.*)\)')
    match = pattern.finditer(s)
    for a in match:
        if a:
            text, url = a.group(1,2)
            x, y = a.span()
            s = s[:x] + "<img src=" + url + " target=\"_blank\">" + "</a>" + s[y:]

    # 角标
    pattern = re.compile(r'(.)\^\[([^\]]*)\]')
    match = pattern.finditer(s)
    k = 0
    for a in match:
        if a:
            sym,index = a.group(1,2)
            x, y = a.span()
            s = s[:x+8*k] + sym + "<sup>" + index + "</sup>" + s[y+8*k:]
        k += 1

    return s
