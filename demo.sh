#!/bin/sh

mkdir -p demo
cd demo

PYEND="../src/pyend/pyend.py"

echo removing all end marks...
echo python3 $PYEND --april $PYEND -s --out pyend.noend.py
python3 $PYEND --april $PYEND -s --out pyend.noend.py
echo

echo inserting end marks...
echo python3 $PYEND --april pyend.noend.py -e --out pyend.end.py
python3 $PYEND --april pyend.noend.py -e --out pyend.end.py
echo

echo comparing...
echo diff -s pyend.end.py $PYEND
diff -s pyend.end.py $PYEND
echo

echo removing all indentation...
echo "sed 's/	//g' $PYEND > pyend.noindent.txt"
sed 's/	//g' $PYEND > pyend.noindent.txt
echo

echo restoring indentation...
echo python3 $PYEND --april pyend.noindent.txt -i --out pyend.reindent.py
python3 $PYEND --april pyend.noindent.txt -i --out pyend.reindent.py
echo

echo comparing...
echo diff -s $PYEND pyend.reindent.py
diff -s $PYEND pyend.reindent.py
echo