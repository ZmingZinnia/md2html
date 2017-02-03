"""md2pdf

translates markdown file into html or pdf, and support picture insertion.abs

Usage:
    md2pdf <sourcefile> <outputfile> [options]

Options:
    -h --help           show help document.
    -v --version        show version information.
    -o --output         translate sourcefile into html file.
    -p --print          translate sourcefile into pdf file and html file respectively.
    -P --Print          translate sourcefile into pdf file only.
"""

import os
import sys,getopt

from parse import *

__version__ = '1.0'

need_mathjax =False


def run(source_file, dest_file, dest_pdf_file, only_pdf):
    # 获取文件名
    file_name = source_file
    # 转换后的 HTML 文件名
    dest_name = dest_file
    # 转换后的 PDF文件名
    dest_pdf_name = dest_pdf_file

    # 获取文件后缀
    _, suffix = os.path.splitext(file_name)
    if suffix not in [".md",".markdown",".mdown","mkd"]:
        print('Error: the file should be in markdown format')
        sys.exit(1)

    if only_pdf:
        dest_name = ".~temp~.html"


    f = open(file_name, "r")
    f_r = open(dest_name, "w")

    # 往文件中填写 HTML 的一些属性
    f_r.write("""<style type ="text/css">div {display: block;font-family: "Times New Roman",\
    Georgia,Serif}#wrapper { width: 100%;height:100%; margin: 0;padding: 0;}#left { float:left;\
    width:10%; height: 100%;}#second {  float:left; width:80%;height:100%;}#right {float:left;\
    width:10%; height:100%;}</style><div id ="wrapper"><div id="left"></div><div id="second">""")
    #f_r.write("""<meta charset="utf-8/>""")

    # 逐行解析 markdown 文件
    for eachline in f:
        result = parse(eachline)
        if result != "":
            f_r.write(result)

    #f_r.write("""<br><br></div><div   id="right"></div></div>""")

    # 公式支持
    global need_mathjax
    if need_mathjax:
        f_r.Write("""<script type="text/x-mathjax-config">MathJax.Hub.Config({\
        text2jax: {inlineMath: [['$','$'],[''\\
        (','\\)']]}});\
        </script><script type="text/javascript" \
        src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>""")
        # 文件操作之后关闭
        f_r.close()
        f.close()

        # 调用扩展 wkhtmltopdf 将 HTML 文件转换成 PDF
        if dest_pdf_name != "" or only_pdf:
            call(["wkhtmltopdf", dest_name, dest_pdf_name])
        # 如果有必要，删除中间过程生成的 HTML 文件
        if only_pdf:
            call(["rm",dest_name])


# 主函数
def main():
    # 定义输出的 html 文件默认文件名
    dest_file = "translation_result.html"
    # 定义输出的 pdf 文件的默认文件名
    dest_pdf_file = "translation_result.pdf"
    # 该选项决定了是否保留作为转化的 HTML 临时文件
    only_pdf = False

    # 使用帮助文档构建命令解析器
    args = docopt(__doc__, version=__version__)

    dest_file = args['<outputfile>'] if args['--output'] else dest_file

    dest_file = args['<outputfile>'] if args['--print'] or args['--Print'] else ""
    #进行解析
    run(args['<sourcefile>'], dest_file, dest_pdf_file, args['--Print'])

    
if __name__=="__main__":
   # try:
    main()
    #except Exception as result:
     #   print(result)
