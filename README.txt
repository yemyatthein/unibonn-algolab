Developed for the Lab course at University of Bonn during my Master's study. The course is about implementing a selected efficient algorithm. My assigned paper is about min-cost flow algorithm and the paper is written by Dr.James Orlin, MIT. The paper can be seen here http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.90.6425&rep=rep1&type=pdf

Two algorithms included:
    Edmond-Karp algorithm
    James Orlin sclaing algorithm

Wrritten in Python and used NetworkX library for graph implementation.


Package structure:

The package contains two source code files and two folders. The source code files are implementation of Edmonds-Karp RHS scaling algorithm (edmonds_karp.py) and Orlin's Strongly Polynomial algorithm (orlin.py). The "input" folder contain 5 input files and "visual.pdf" which illustrates those 5 examples. The folder "doc" contains presentation files: Powerpoint file and PDF file.

How to run:

In order to run, from command line, you can run the python file and it will ask you for the input file name. For example, you can specify like this "./input/input_1.txt". Input data format is provided in all of the sample input file. In the input file, lines started with "##" are comments.