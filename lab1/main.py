from LineProcessor import *
from CCodeAnalyzer import *


def main():
    lp = LineProcessor("input.txt")
    code = ''.join(lp.delete_newlines())
    analyzer = CCodeAnalyzer(code=code)
    print(analyzer.analyze())
    


main()

