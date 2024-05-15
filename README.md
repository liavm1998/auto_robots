# autonmous robots assignments
## ex0
<h6>submitters</h6>
<p>name:liav levi ID:206603193</p>
<p>name:oria tzadok ID:315500157</p>
<p>name:sagi yosef azulai ID:207544230</p>

## HOW TO RUN
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

## little code explanation

<h3>this should be very easy as the function names do literaly as they named</h3>
<p><b>log_to_measurment</b>: as it sound this function accept the log file location and load it as pandas.DataFrame</p>
<p><b>format_satelite_ID</b>: parse the columns Svid and ConstellationType to satPRN which will be the unique id of the satelite</p>
<p><b>handle_numeric_cols</b>:take the log dataframe and parse the numeric columns in it to be well ... numeric</p>
<p><b>calculate_datetime_cols</b>: calculate DateTime related columns such as pseudorange_seconds and Epoch from TimeNanos, FullBiasNanos and etc</p>
<p><b>clause2</b>: accept input file and parse it to satelite locations csv</p>
<p><b>clause3</b>: accept thdata from clause2 and calculate the log ecef(earth centered earth focused ) positions using weighted_least_squares algorithm</p>
<p><b>weighted_least_squares</b>:like any regression algorithm  iteratively refines the estimated receiver position and clock bias until convergence, aiming to minimize the difference between measured and estimated pseudoranges. wls is more appropriate as there is heteroscedasticity in the data, meaning that the variance of the errors varies across the range of the independent variable.</p>
<p><b>main</b>: run clause2 and then clause3 by then generate </p>
