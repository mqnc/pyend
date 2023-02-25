#!/bin/sh

echo removing all end marks...
echo python3 pyend.py pyend.py -s --out pyend.noend.py
python3 pyend.py pyend.py -s --out pyend.noend.py
echo

echo inserting end marks...
echo python3 pyend.py pyend.py -e --out pyend.end.py
python3 pyend.py pyend.py -e --out pyend.end.py
echo

echo comparing...
echo diff -s pyend.end.py pyend.py
diff -s pyend.end.py pyend.py
echo

echo removing all indentation...
echo sed 's/	//g' pyend.py > pyend.noindent.txt
sed 's/	//g' pyend.py > pyend.noindent.txt
echo

echo restoring indentation...
echo python3 pyend.py pyend.noindent.txt -i --out pyend.reindent.py
python3 pyend.py pyend.noindent.txt -i --out pyend.reindent.py
echo

echo comparing...
echo diff -s pyend.py pyend.reindent.py
diff -s pyend.py pyend.reindent.py
echo