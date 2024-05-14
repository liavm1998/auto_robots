
# ex0
<h3>submitters</h3>
<p>name:liav levi ID:206603193</p>
<p>name:oria tzadok ID:315500157</p>
<p>name:sagi yosef azulai ID:0000000000</p>

# 
<p> first thing to do for this assignment running and checking: </p>


~~~
cd ex0 
pip install -r requirements.txt 
~~~

<p> if you are using windows you may need to install with --user flag like this:</p>
~~~
pip install -r requirements.txt --user
~~~

<p> to run the assignment</p>
~~~
python gnss_parser.py <input_file.txt>
~~~

<p> to run the tests(we disable warning as we use old version of pandas and)</p>

~~~
pytest --disable-warnings
~~~

<p> to clean the unwanted files you can run</p>

~~~
python cleaner.py
~~~