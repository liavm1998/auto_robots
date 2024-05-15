# autonmous robots assignments
## ex0
<h6>submitters</h6>
<p>name:liav levi ID:206603193</p>
<p>name:oria tzadok ID:315500157</p>
<p>name:sagi yosef azulai ID:0000000000</p>

# HOW TO RUN
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

<p> to run the tests(we disable warning as we use old version of pandas and numpy)</p>

~~~
pytest --disable-warnings
~~~


<p> to clean the unwanted files you can run</p>

~~~
python cleaner.py
~~~

# little code explanation
this should be very easy as the function names do literaly as they named
log_to_measurment: as it sound this function accept the log file location and load it as pandas.DataFrame
format_satelite_ID: parse the columns Svid and ConstellationType to satPRN which will be the unique id of the satelite
handle_numeric_cols:take the log dataframe and parse the numeric columns in it to be well ... numeric
calculate_datetime_cols: calculate DateTime related columns such as pseudorange_seconds and Epoch from TimeNanos, FullBiasNanos and etc
clause2: accept input file and parse it to satelite locations csv
clause3: accept thdata from clause2 and calculate the log ecef(earth centered earth focused ) positions using weighted_least_squares algo
main: run clause2 and then clause3 by then generate 