----------------------------------    TO_RUN    --------------------------------------------
Remove-Item -Recurse -Force venv
python -m venv venv



.\venv\Scripts\activate



pip install -r requirements.txt
---------------------------------------------------------------------------------------------




---------------------------------------------------------------------------------------------
1. POSE_PATH = 'yolov8m-pose.pt'
#can pose use medium and other use nano?

2. Shoplifting model tuning

3. warning sound

4. UI desin

5. Database with analysis (ongoing)
#Option 2: Supabase (Best for SQL/Dashboarding)
-summary log file upload to firebase per hour

6. Retrain all model using yolov8m (ongoing)

7. detect customer skin and cloth color and characteristic (ongoing)

8. 3d body detection (Expose github) (ongoing) ignore?

9. Allow user to switch between 2d model and 3d model (ongoing)
---------------------------------------------------------------------------------------------




---------------------------------------------------------------------------------------------
*4Feb meeting*

1.MAP
2.AP
3.IoU
Metrics
#need to mention in chap5

firebase realtime Database
-save in base64 image python

multithread in python
-allow multiple cpu code to work in optimised way

re-identifcation
-people out of area then come back still can detect

rtsp ip camera
-use phone as the ip camera
-collect datetime,evnt happened and location(country, state, street)

clear gpu model in python
-after allowing user to select specific model to use

UI interface
-be more customize
-allow user to upload file for detection

can try to tune is better

draw the epoch graph to determine the increasing trend until which epoch (accuracy graph)
---------------------------------------------------------------------------------------------

13 Feb meeting
to_do
1. one more window to view image save to firebase?

chap3
-EDA
-explain dataset details
-how to train own model-how many model
include formula and explain for:(metric mesurement)
-MAP
-AP
-recall


chap4
-website brower
-input output

chap5
-result table
-support self train model

chap6
-conclusion

week7/8 check report

eelin: Hyperbolic graph