################################################################################
#                          The BrainFuck to C Compiler                         #
################################################################################
# The BrainFuck to C Compiler (BFCC) is a ruby program that compiles Brainfuck
# code into C code. BFCC takes Brainfuck code via the STDIN stream, and outputs
# C code to the STDOUT stream.
# 
# If any errors occur, a debugging message will be printed to the STDERR stream
# and the program will exit immediately with a failure exit code. No output
# will be printed to STDOUT upon failure.
# 
# NOTE: the memory `tape` wraps when the pointer reaches its ends.
################################################################################
#                                     USAGE                                    #
################################################################################
# Run:
#     ruby bfcc.rb BSS_SIZE < in.b > out.c
# where BSS_SIZE is a positive integer corresponding to the `tape` size in
# bytes, in.b is the input file, and out.c is the output file.
# 
# For example
#     ruby bfcc.rb 256 < helloworld.b > helloworld.c
# compiles the attached helloworld Brainfuck program to c.
################################################################################
#                                    LICENSE                                   #
################################################################################
# MIT License
# 
# Copyright (c) 2020 Theodore Preduta
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
################################################################################

BSS_SIZE = ARGV[0].to_i

if BSS_SIZE <= 0 then
  STDERR << "BSS size must be a positive integer.\n"
  exit false
end

text_buffer = ""
loop_level = 0
line_number = 1

STDIN.read.each_char do |c|
  case c
  when "\n"
    line_number += 1
  when '>'
    text_buffer << "p++;if(p>=t)p=0;"
  when '<'
    text_buffer << "p--;if(p<0)p=t;"
  when '+'
    text_buffer << "m[p]++;"
  when '-'
    text_buffer << "m[p]--;"
  when '.'
    text_buffer << "r(m[p]);"
  when ','
    text_buffer << "m[p]=g();"
  when '['
    text_buffer << "d{"
    loop_level += 1
  when ']'
    text_buffer << "}w(m[p]);"
    loop_level -= 1
  end

  if loop_level < 0 then
    STDERR << "Mismatched loops on line #{line_number}.\n"
    exit false
  end
end

if loop_level != 0 then
  STDERR << "Mismatched loops on line #{line_number}.\n"
  exit false
end

STDOUT << "#include <stdio.h>\n#define d do\n#define g getchar\n#define r putchar\n#define t #{BSS_SIZE}\n#define w while\nunsigned char m[#{BSS_SIZE}];int p;int main(){#{text_buffer}}".encode("utf-8")